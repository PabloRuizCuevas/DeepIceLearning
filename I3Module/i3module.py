# coding: utf-8

import sys
import os
print(os.system("nvidia-smi"))
os.environ["TF_USE_CUDNN"] = "0"
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname,'./i3module.sh'), 'r') as f:
    x=f.read().splitlines()
for i in x:
    if '#' in i: continue
    if 'PY_ENV=' in i: break
sys.path.insert(0,os.path.join(i.split('=')[1], 'lib/python2.7/site-packages/'))
sys.path.insert(0, os.path.join(dirname, 'lib/'))
sys.path.insert(0, os.path.join(dirname, 'models/'))
from model_parser import parse_functional_model
from helpers import *
import numpy as np
from icecube import icetray
from I3Tray import I3Tray
from configparser import ConfigParser
from collections import OrderedDict
import time
from icecube.dataclasses import I3MapStringDouble
from icecube import dataclasses, dataio
import argparse
from plotting import figsize, make_plot, plot_prediction
from keras.backend.tensorflow_backend import set_session
import tensorflow as tf

class DeepLearningClassifier(icetray.I3ConditionalModule):
    """IceTray compatible class of the  Deep Learning Classifier
    """

    def __init__(self,context):
        """Initialize the Class
        """
        icetray.I3ConditionalModule.__init__(self, context)
        self.AddParameter("pulsemap","Define the name of the pulsemap",
                          "InIceDSTPulses")
        self.AddParameter("save_as", "Define the Output key",
                          "Deep_Learning_Classification")
        self.AddParameter("batch_size", "Size of the batches", 40)
        self.AddParameter("n_cores", "number of cores to be used", 4)
        self.AddParameter("keep_daq", "whether or not to keep Q-Frames", True)
        self.AddParameter("model", "which model to use", 'classification')

    def Configure(self):
        """Read the network architecture and input, output information from config files
        """

        print('Initialize the Deep Learning classifier..this may take a few seconds')
        self.__runinfo = np.load(os.path.join(dirname,'models/{}/run_info.npy'.format(self.GetParameter("model"))),
                                 allow_pickle=True)[()]
        self.__grid = np.load(os.path.join(dirname, 'lib/grid.npy'),
                              allow_pickle=True)[()]
        self.__inp_shapes = self.__runinfo['inp_shapes']
        self.__out_shapes = self.__runinfo['out_shapes']
        self.__inp_trans = self.__runinfo['inp_trans']
        self.__out_trans = self.__runinfo['out_trans']
        self.__pulsemap = self.GetParameter("pulsemap") 
        self.__save_as =  self.GetParameter("save_as")
        self.__batch_size =  self.GetParameter("batch_size")
        self.__n_cores =  self.GetParameter("n_cores")
        self.__keep_daq = self.GetParameter("keep_daq") 
        self.__frame_buffer = []
        self.__buffer_length = 0
        self.__num_pframes = 0
        print("Pulsemap {},  Store results under {}".format(self.__pulsemap,self.__save_as))
        exec 'import models.{}.model as func_model_def'.format(self.GetParameter("model"))
        self.__output_names = func_model_def.output_names
        self.__model = func_model_def.model(self.__inp_shapes, self.__out_shapes)
        config = tf.ConfigProto(intra_op_parallelism_threads=self.__n_cores,
                                inter_op_parallelism_threads=self.__n_cores,
                                device_count = {'GPU': 1 , 'CPU': 1},
                                log_device_placement=True)
        sess = tf.Session(config=config)
        set_session(sess)
        self.__model.load_weights(os.path.join(dirname, 'models/{}/weights.npy'.format(self.GetParameter("model"))))
        dataset_configparser = ConfigParser()
        dataset_configparser.read(os.path.join(dirname,'models/{}/config.cfg'.format(self.GetParameter("model"))))
        inp_defs = dict()
        for key in dataset_configparser['Input_Times']:
            inp_defs[key] = dataset_configparser['Input_Times'][key]
        for key in dataset_configparser['Input_Charges']:
            inp_defs[key] = dataset_configparser['Input_Charges'][key]
        self.__inputs = []
        for key in self.__inp_shapes.keys():
            binput = []
            branch = self.__inp_shapes[key]
            for bkey in branch.keys():
                if bkey == 'general':
                    continue
                elif 'charge_quantile' in bkey:
                    feature = 'pulses_quantiles(charges, times, {})'.format(float('0.' + bkey.split('_')[3]))
                else:
                    feature = inp_defs[bkey.replace('IC_','')]
                trans = self.__inp_trans[key][bkey]
                binput.append((feature, trans))
            self.__inputs.append(binput)

    def BatchProcessBuffer(self, frames):
        """Batch Process a list of frames. This includes pre-processing, prediction and storage of the results  
        """        
        timer_t0 = time.time()
        f_slices = []
        if self.__num_pframes == 0:
            return
        for frame in frames:
            if frame.Stop != icetray.I3Frame.Physics:
                continue
            pulse_key = self.__pulsemap
            if pulse_key not in frame.keys():
                print('No Pulsemap called {}..continue without prediction'.format(pulse_key))
                return
            f_slice = []
            t0 = get_t0(frame, puls_key=pulse_key)
            pulses = frame[pulse_key].apply(frame)
            for key in self.__inp_shapes.keys():
                f_slice.append(np.zeros(self.__inp_shapes[key]['general']))
            for omkey in pulses.keys():
                dom = (omkey.string, omkey.om)
                if not dom in self.__grid.keys():
                    continue
                gpos = self.__grid[dom]
                charges = np.array([p.charge for p in pulses[omkey][:]])
                times = np.array([p.time for p in pulses[omkey][:]]) - t0
                widths = np.array([p.width for p in pulses[omkey][:]])
                for branch_c, inp_branch in enumerate(self.__inputs):
                    for inp_c, inp in enumerate(inp_branch):
                        f_slice[branch_c][gpos[0]][gpos[1]][gpos[2]][inp_c] = inp[1](eval(inp[0]))
            processing_time = time.time() - timer_t0
            f_slices.append(f_slice)
        predictions = self.__model.predict(np.array(np.squeeze(f_slices, axis=1), ndmin=5),
                                           batch_size=self.__batch_size,
                                           verbose=0, steps=None)
        prediction_time = time.time() - processing_time - timer_t0
        i = 0
        for frame in frames:
            if frame.Stop != icetray.I3Frame.Physics:
                continue
            output = I3MapStringDouble()
            prediction = np.concatenate(np.atleast_2d(predictions[i]))
            for j in range(len(prediction)):
                output[self.__output_names[j]] = float(prediction[j])
            frame.Put(self.__save_as, output)
            i += 1
        tot_time = time.time() - timer_t0
        print('Total Time {:.2f}s [{:.2f}s], Processing Time {:.2f}s [{:.2f}s], Prediction Time {:.2f}s [{:.2f}s]'.format(
                tot_time, tot_time/i, processing_time, processing_time/i,
                prediction_time, prediction_time/i))

    def Physics(self, frame):
        """ Buffer physics frames until batch size is reached, then start processing  
        """
        self.__frame_buffer.append(frame)
        self.__buffer_length += 1
        self.__num_pframes += 1
        if self.__buffer_length == self.__batch_size:
            self.BatchProcessBuffer(self.__frame_buffer)
            for frame in self.__frame_buffer:
                self.PushFrame(frame)
            self.__frame_buffer[:] = []
            self.__buffer_length = 0
            self.__num_pframes = 0

    def DAQ(self,frame):
        """ Handel Q-Frames. Append to buffer if they should be kept
        """
        if self.__keep_daq:
            self.__frame_buffer.append(frame)

    def Finish(self):
        """ Process the remaining (incomplete) batch of frames  
        """
        self.BatchProcessBuffer(self.__frame_buffer)
        for frame in self.__frame_buffer:
            self.PushFrame(frame)
        self.__frame_buffer[:] = []


def print_info(phy_frame):
    print('Run_ID {} Event_ID {}'.format(phy_frame['I3EventHeader'].run_id,
                                         phy_frame['I3EventHeader'].event_id))
    print(phy_frame["Deep_Learning_Classification"])
    return


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--files", help="files to be processed",
        type=str, nargs="+", required=True)
    parser.add_argument(
        "--plot", action="store_true", default=False)
    parser.add_argument(
        "--pulsemap", type=str, default="InIceDSTPulses")
    parser.add_argument(
        "--batch_size", type=int, default=40)
    parser.add_argument(
        "--n_cores", type=int, default=4)
    parser.add_argument(
        "--keep_daq", action='store_true', default=False)
    parser.add_argument(
        "--model", type=str, default='classification')    
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parseArguments()
    files = []
    for j in np.atleast_1d(args.files):
        if os.path.isdir(j):
            files.extend([os.path.join(j,i) for i in os.listdir(j) if '.i3' in i])
        else:
            files.append(j)
    files = sorted(files)
    tray = I3Tray()
    tray.AddModule('I3Reader','reader',
                   FilenameList = files)
    tray.AddModule(DeepLearningClassifier, "DeepLearningClassifier",
                   pulsemap=args.pulsemap,
                   batch_size=args.batch_size,
                   n_cores=args.n_cores,
                   keep_daq=args.keep_daq,
                   model=args.model)
    tray.AddModule(print_info, 'printer',
                   Streams=[icetray.I3Frame.Physics])
    tray.AddModule("I3Writer", 'writer',
                   Filename=os.path.expanduser("~/myhdf.i3.bz2"))
    if args.plot:
        tray.AddModule(make_plot, 'plotter',
                       Streams=[icetray.I3Frame.Physics])
    tray.Execute()
    tray.Finish()

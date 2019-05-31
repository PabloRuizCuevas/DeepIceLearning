#!/usr/bin/env python

import pydag
import datetime
import os
import argparse
import time
import numpy as np
from configparser import ConfigParser
import cPickle as pickle
import math


def get_inds(k , ratio):
    n_chunks = round(k/ratio)
    inds_pre = np.arange(0, (n_chunks+1) * math.floor(ratio), math.floor(ratio))
    for j, val in enumerate(np.arange(0, k - inds_pre[-1])[::-1]):
        inds_pre[-(j+1)] += val
    return inds_pre


def parseArguments():
    # Create argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset_config",
        help="dataset config ",
        type=str, default='create_dataset.cfg')
    parser.add_argument(
        "--files_per_job",
        help="n files per job ", default=50,
        type=int)
    parser.add_argument(
        "--name",
        help="Name for the Dagman Files",
        type=str, default='create_dataset')
    parser.add_argument(
        "--request_RAM",
        help="amount of RAM in GB",
        type=int, default=4)
    parser.add_argument(
        "--compression_format",
        help="which compression format to use",
        type=str, default='i3.bz2')
    parser.add_argument(
        "--rescue",
        help="Run rescue script?!",
        type=str, default='')
    args = parser.parse_args()
    return args.__dict__


if __name__ == '__main__':
    print "\n ############################################"
    print "You are running the script with arguments: "
    args = parseArguments()
    for a in args:
        print str(a) + ": " + str(args[a])
    print"############################################\n "
    Resc = args["rescue"]
    if Resc == '':
        dataset_parser = ConfigParser()
        dataset_parser.read(args['dataset_config'])
        today = str(datetime.datetime.now()).\
            replace(" ", "-").split(".")[0].replace(":", "-")

        PROCESS_DIR = os.path.join(dataset_parser.get("Basics", "dagman_folder"),
                                   today)
        if not os.path.exists(PROCESS_DIR):
            os.makedirs(PROCESS_DIR)

        WORKDIR = os.path.join(PROCESS_DIR, "jobs/")
        script = os.path.join(
            dataset_parser.get("Basics", "thisfolder"),
            'submit_scripts/create_dataset_env.sh')
        print('Submit Script:\n {}'.format(script))

        dag_name = args["name"]
        dagFile = os.path.join(
            WORKDIR, "job_{}.dag".format(dag_name))
        submitFile = os.path.join(WORKDIR, "job_{}.sub".format(dag_name))
        if not os.path.exists(WORKDIR):
            os.makedirs(WORKDIR)
            print("Created New Folder in: {}".format(WORKDIR))

        log_path = os.path.join(PROCESS_DIR, "logs/{}/".format(dag_name))
        if not os.path.exists(log_path):
            os.makedirs(log_path)
            print("Created New Folder in: {}".format(log_path))

        print("Write Dagman Files to: {}".format(submitFile))
        RAM_str = "{} GB".format(args["request_RAM"])
        arguments = " --filelist $(PATHs) --dataset_config $(DATASET) "
        submitFileContent = {"universe": "vanilla",
                             "notification": "Error",
                             "log": "$(LOGFILE).log",
                             "output": "$(STREAM).out",
                             "error": "$(STREAM).err",
                             "initialdir" : "/home/tglauch/",
        #		             "Requirements" : "HAS_CVMFS_icecube_opensciencegrid_org",
        #                    "Requirements" : '(Machine != "n-15.icecube.wisc.edu")',
                             "request_memory": RAM_str,
                             "arguments": arguments}
        submitFile = pydag.htcondor.HTCondorSubmit(submitFile,
                                                   script,
                                                   **submitFileContent)
        submitFile.dump()
        folderlist = dataset_parser.get("Basics", "folder_list")
        basepath = [dataset_parser['Basics'][key] for key in
                    dataset_parser['Basics'].keys() if 'mc_path' in key]
        filelist = dataset_parser.get("Basics", "file_list")
        file_bunches = []
        print(basepath)
        if folderlist == 'allinmcpath':
            folderlists = []
            for p in basepath:
                tlist = []
                for root, dirs, files in os.walk(p):
                    print root
                    a =  [s_file for s_file in files
                         if s_file[-len(args['compression_format']):] == args['compression_format']]
                    if len(a) > 0:
                        tlist.append(root)
                print len(tlist)
                folderlists.append(tlist)
        else:
            folderlists = [[folder.strip() for folder in folderlist.split(',')]]

        if not filelist == 'allinfolder':
            filelist = filelist.split(',')
        num_files = []
        print folderlists
        run_filelist = []
        for j, bfolder in enumerate(folderlists):

            run_filelist.append([])
            for subpath in bfolder:
                files = [f for f in os.listdir(subpath) if not os.path.isdir(f)]
                i3_files_all = [s_file for s_file in files
                                if s_file[-len(args['compression_format']):] == args['compression_format']]
                print len(i3_files_all)
                if not filelist == 'allinfolder':
                    i3_files = [f for f in filelist if f in i3_files_all]
                else:
                    i3_files = i3_files_all
                b = [os.path.join(subpath, s_file) for s_file in i3_files]
                run_filelist[j].extend(b)
        filesjob = 1.*args['files_per_job']*np.array([len(k) for k in run_filelist])/np.min([len(k) for k in run_filelist])
        inds = [get_inds(len(k), filesjob[i]) for i,k in enumerate(run_filelist)]
        for j, rfilelist in enumerate(run_filelist):
            outfolder = os.path.join(dataset_parser.get('Basics', 'out_folder'),
                                     "filelists/dataset", str(j))
            if not os.path.exists(outfolder):
                os.makedirs(outfolder)
                print('Created Folder {}'.format(outfolder))
            nfiles = int(round(filesjob[j]))
            print inds[j][10]
            save_list = [rfilelist[int(inds[j][i]):int(inds[j][i+1])] for i
                         in range(len(inds[j])-1)]
            print('Save filelists for mc  {}'.format(basepath[j]))
            num_files.append(len(save_list))
            for c, sublist in enumerate(save_list):
                with open(os.path.join(outfolder,'File_{}.pickle'.format(c)), 'w+') as f:
                        pickle.dump(sublist, f)

        nodes = []
        print('The number of files for the datasets is {} '.format(num_files))
        print('Resulting in {} jobs'.format(np.min(num_files)))
        for i in range(np.min(num_files)):
            fname = 'File_{}'.format(i)
            logfile = os.path.join(log_path,fname)
            stream = os.path.join('/data/user/tglauch/condor', fname)
            PATH = ''
            for k in range(len(basepath)):
                PATH = PATH +\
                    os.path.join(dataset_parser.get('Basics', 'out_folder'),
                                 "filelists/dataset",
                                 str(k),
                                 '{}.pickle'.format(fname)) + " "
            dagArgs = pydag.dagman.Macros(LOGFILE=logfile,
                                          PATHs=PATH,
                                          STREAM = stream,
                                          DATASET=args['dataset_config'])
            node = pydag.dagman.DAGManNode(i, submitFile)
            node.keywords["VARS"] = dagArgs
            nodes.append(node)
        dag = pydag.dagman.DAGManJob(dagFile, nodes)
        dag.dump()
    else:
        dagFile = Resc
    os.system("condor_submit_dag -f " + dagFile)
    time.sleep(1)

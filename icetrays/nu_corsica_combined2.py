from icecube import dataio,icetray
from icecube import dataclasses
import icecube.MuonGun
import numpy as np
import os
import sys
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.join(os.path.abspath(".."),'lib'))
sys.path.append("/data/user/pruiz/DeepIceLearning/lib")
sys.path.append("/data/user/pruiz/DeepIceLearning")
print(sys.path)
import lib.reco_quantities as reco_q
from I3Tray import *

#os.listdir()
#argparse
print("directory",sys.argv[1])

geo_file=sys.argv[2]
print("geo file",sys.argv[2])
list0 = [os.path.join(sys.argv[1], i) for i in os.listdir(sys.argv[1])]


def run(i3_file,geo_file):
    """IceTray script that wraps around an i3file and fills the events dict
       that is initialized outside the function

    Args:
        i3_file, and IceCube I3File
    Returns:
        True (IceTray standard)
    """

    # Initialize
    events = dict()
    events['reco_vals'] = []
    events['pulses'] = []
    events['waveforms'] = []
    events['pulses_timeseries'] = []
    events['t0'] = []
    surface = icecube.MuonGun.ExtrudedPolygon.from_file(geo_file, padding=0)
    def save_to_array(phy_frame):
        """Save the waveforms pulses and reco vals to lists.

        Args:
            phy_frame, and I3 Physics Frame
        Returns:
            True (IceTray standard)
        """
        reco_arr = []
        pulses = None
        for el in settings:
            if el[1] == pulsemap_key:
                try:
                    pulses = phy_frame[pulsemap_key].apply(phy_frame)
                except Exception as inst:
                    print('Failed to add pulses {} \n {}'.format(el[1], inst))
                    print inst
                    return False
            elif el[0] == 'variable':
                try:
                    reco_arr.append(eval('phy_frame{}'.format(el[1])))
                except Exception as inst:
#                    print inst
                    reco_arr.append(np.nan)
            elif el[0] == 'function':
                try:
                    reco_arr.append(
                        eval(el[1].replace('_icframe_', 'phy_frame, geometry_file')))
                except Exception as inst:
                    print('Failed to evaluate function {} \n {}'.format(el[1], inst))
                    return False
        if pulses is not None:
            tstr = 'Append Values for run_id {}, event_id {}'
            eheader = phy_frame['I3EventHeader']
            print(tstr.format(eheader.run_id, eheader.event_id))
            events['t0'].append(get_t0(phy_frame))
            events['pulses'].append(pulses)
            events['reco_vals'].append(reco_arr)
        else:
            print('No pulses in Frame...Skip')
            return False
        return

    tray = I3Tray()
    tray.AddModule("I3Reader","source", FilenameList=i3_file)
    tray.AddModule( reco_q.classify_wrapper, "classify",surface=surface,Streams=[icetray.I3Frame.Physics])
    tray.AddModule( reco_q.track_length_in_detector, 'track_length', surface=surface,Streams=[icetray.I3Frame.Physics])
    print()
    print(phy_frame)   #TrayInfo()  keyword argument 'gcdfile' keyword argument 'surface' 'key' 'surface'
    print()
    #tray.AddModule( save_to_array, 'save',Streams=[icetray.I3Frame.Physics])

    print("Saving")
    #save_to_array('track_length')

    tray.Execute()
    tray.Finish()
    print("finish!")

run(list0[0:10],geo_file)

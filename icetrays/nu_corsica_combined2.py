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
#print("directory",sys.argv[1])

geo_file=sys.argv[2]
#print("geo file",sys.argv[2])
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
    surface = icecube.MuonGun.ExtrudedPolygon.from_file(geo_file, padding=0)

    events['track_length'] = []
    events['track_length'] = []
    def save_array(phy_frame):
        events['track_length'].append(phy_frame['track_length'].value)
        events['classify'].append(phy_frame['classify'].value)

    tray = I3Tray()
    tray.AddModule("I3Reader","source", FilenameList=i3_file)
    tray.AddModule( reco_q.classify_wrapper, "classify",surface=surface,Streams=[icetray.I3Frame.Physics])
    tray.AddModule( reco_q.track_length_in_detector, 'track_length', surface=surface,Streams=[icetray.I3Frame.Physics])
    tray.AddModule(save_array,"save")

    #tray.AddModule( save_to_array, 'save',Streams=[icetray.I3Frame.Physics])
    #save_to_array('track_length')
    tray.Execute()
    tray.Finish()

    print("finish!")
    print(events)
    print(events['classify'])
    np.save("track_length", events)


run(list0[0:10],geo_file)

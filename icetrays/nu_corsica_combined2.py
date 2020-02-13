from icecube import dataio,icetray
from icecube import dataclasses
from I3Tray import *
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.join(os.path.abspath(".."),'lib'))
import lib.reco_quantities as reco_q

# I3Tray Defintion
tray = I3Tray()
tray.AddModule("I3Reader","source", FilenameList=[i3_file])
tray.AddModule(reco_q.classify_wrapper, "classify",surface=surface,Streams=[icetray.I3Frame.Physics])
tray.AddModule(reco_q.track_length_in_detector, 'track_length', surface=surface,Streams=[icetray.I3Frame.Physics])

tray.Execute()
tray.Finish()

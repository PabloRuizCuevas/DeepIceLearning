from icecube import dataio,icetray
from icecube import dataclasses
from I3Tray import *
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.join(os.path.abspath(".."),'lib'))
import lib.reco_quantities as reco_q

def save_to_array(phy_frame):

    """
    Save the waveforms pulses and reco vals to lists.

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
#               print inst
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


# I3Tray Defintion
tray = I3Tray()
tray.AddModule("I3Reader","source", FilenameList=[i3_file])
tray.AddModule(reco_q.classify_wrapper, "classify",surface=surface,Streams=[icetray.I3Frame.Physics])
tray.AddModule(reco_q.track_length_in_detector, 'track_length', surface=surface,Streams=[icetray.I3Frame.Physics])
tray.AddModule(save_to_array, 'save',Streams=[icetray.I3Frame.Physics])


tray.Execute()
tray.Finish()

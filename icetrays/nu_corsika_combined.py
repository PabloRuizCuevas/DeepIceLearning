from icecube import dataio, icetray, WaveCalibrator
from icecube import dataclasses, paraboloid, simclasses, recclasses, spline_reco
from I3Tray import *
import sys
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.join(os.path.abspath(".."),'lib'))
import lib.i3mods
import lib.reco_quantities as reco_q
from lib.functions_create_dataset import get_t0
import numpy as np
import random
from icecube.weighting.fluxes import GaisserH4a
from icecube.weighting import weighting, get_weighted_primary
import icecube.MuonGun
def cuts(phy_frame):
    """Performe a pre-selection of events according
       to the cuts defined in the config file

    Args:
        phy_frame, and IceCube I3File
    Returns:
        True (IceTray standard)
    """

    #if 'CorsikaWeightMap' in phy_frame.keys():
    #    if ['CorsikaWeightMap']['Multiplicity'] > 1.:
    #        print('Multiplicity > 1')
    #        return False
#    if phy_frame["mu_E_on_entry"].value == 0.:
#        print("mu_E_on_entry is 0")
#        return False
   # elif phy_frame["track_length"].value < 100:
   #     print("track length smaller than 100m")
   #     return False
#    else:
    return True


def print_info(phy_frame):
    print('run_id {} ev_id {} dep_E {} classification {}  signature {} track_length {}'.format(
          phy_frame['I3EventHeader'].run_id, phy_frame['I3EventHeader'].event_id,
          phy_frame['depE'].value, phy_frame['classification'].value,
          phy_frame['signature'].value, phy_frame['track_length'].value))
    return


generator = 1000*weighting.from_simprod(11499) + 1785*weighting.from_simprod(11362)
flux = GaisserH4a()

def add_weighted_primary(phy_frame):
    if not 'MCPrimary' in phy_frame.keys():
        get_weighted_primary(phy_frame)
    return

def corsika_weight(phy_frame):
    if 'I3MCWeightDict' in phy_frame:
        return
    energy = phy_frame['MCPrimary'].energy
    ptype = phy_frame['MCPrimary'].pdg_encoding
    weight = flux(energy, ptype)/generator(energy, ptype)
    print('Corsika Weight {}'.format(weight))
    phy_frame.Put("corsika_weight", dataclasses.I3Double(weight))
    return

def get_stream(phy_frame):
    ##maybe conditions in steps ara faster.
    if (phy_frame['I3EventHeader'].sub_event_stream == 'InIceSplit') & (phy_frame['I3EventHeader'].sub_event_id==0) & (phy_frame['track_length'].value>5) & (phy_frame['classification'].value==5):
        if (np.cos(phy_frame['true_zen'])) & (random.uniform(0,1)*np.cos(phy_frame['true_zen'])<0.2):
            return True
    if (phy_frame['I3EventHeader'].sub_event_stream == 'InIceSplit') & (phy_frame['I3EventHeader'].sub_event_id==0) & (phy_frame['classification'].value==1):
        if (random.uniform(0,1)>0.75):   #drop some random events to have more equal distributions
            return True
    if (phy_frame['I3EventHeader'].sub_event_stream == 'InIceSplit') & (phy_frame['I3EventHeader'].sub_event_id==0) &

    else:
        return False



def run(i3_file, num_events, settings, geo_file, pulsemap_key):
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

    # I3Tray Defintion
    tray = I3Tray()
    tray.AddModule("I3Reader", "source",
                   FilenameList=[geo_file,
                                 i3_file])
                                 ##################### add condition module  order matters
    tray.AddModule(reco_q.classify_wrapper, "classify",surface=surface,Streams=[icetray.I3Frame.Physics])
    tray.AddModule(reco_q.track_length_in_detector, 'track_length', surface=surface,Streams=[icetray.I3Frame.Physics])
    tray.AddModule(get_stream, "get_stream",
                    Streams=[icetray.I3Frame.Physics])
    tray.AddModule(add_weighted_primary, "add_primary",
                    Streams=[icetray.I3Frame.Physics])
    tray.AddModule(corsika_weight, 'weighting',
                   Streams=[icetray.I3Frame.Physics])
    tray.AddModule(reco_q.get_primary_nu, "primary_nu",
                    Streams=[icetray.I3Frame.Physics])

    tray.AddModule(reco_q.set_signature, "signature",
                   surface=surface,
                    Streams=[icetray.I3Frame.Physics])
    tray.AddModule(reco_q.first_interaction_point, "v_point",
                   surface=surface,
                    Streams=[icetray.I3Frame.Physics])
    tray.AddModule(reco_q.calc_depositedE, 'depo_energy',
                   surface=surface,
                   Streams=[icetray.I3Frame.Physics])

    tray.AddModule(reco_q.calc_hitDOMs, 'hitDOMs',
                   Streams=[icetray.I3Frame.Physics])
    tray.AddModule(reco_q.get_inelasticity, 'get_inelasticity',
                   Streams=[icetray.I3Frame.Physics])
    tray.AddModule(reco_q.coincidenceLabel_poly, 'coincidence',
                   Streams=[icetray.I3Frame.Physics])
    tray.AddModule(cuts, 'cuts',
                   Streams=[icetray.I3Frame.Physics])
    tray.AddModule(print_info, 'pinfo',
                   Streams=[icetray.I3Frame.Physics])
    ##tray.AddModule(reco_q.mult, 'mult',Streams=[icetray.I3Frame.Physics])       ###my
    tray.AddModule(save_to_array, 'save',
                   Streams=[icetray.I3Frame.Physics])
    if num_events == -1:
        tray.Execute()
    else:
        tray.Execute(num_events)
    tray.Finish()

    return events

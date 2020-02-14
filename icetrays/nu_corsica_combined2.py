from icecube import dataio,icetray
from icecube import dataclasses
import icecube.MuonGun
from I3Tray import *
import numpy as np
import os
import sys


# Generation of the Classification Label
def classify(p_frame, gcdfile=None, surface=None):
    if is_data(p_frame):
        return True
    pclass = 101 # only for security
    if surface is None:
        if gcdfile is None:
            surface = icecube.MuonGun.ExtrudedPolygon.from_I3Geometry(p_frame['I3Geometry'])
        else:
            surface = icecube.MuonGun.ExtrudedPolygon.from_file(gcdfile, padding=0)
    I3Tree = p_frame['I3MCTree']
    neutrino = find_all_neutrinos(p_frame)
    children = I3Tree.children(neutrino)
    p_types = [np.abs(child.pdg_encoding) for child in children]
    p_strings = [child.type_string for child in children]
    p_frame.Put("visible_nu", neutrino)
    IC_hit = np.any([((has_signature(tp, surface) != -1) & np.isfinite(tp.length)) for tp in children])
    if p_frame['I3MCWeightDict']['InteractionType'] == 3 and (len(p_types) == 1 and p_strings[0] == 'Hadrons'):
        pclass = 7  # Glashow Cascade
    else:
        if (11 in p_types) or (p_frame['I3MCWeightDict']['InteractionType'] == 2):
            if IC_hit:
                pclass = 1  # Cascade
            else:
                pclass = 0 # Uncontainced Cascade
        elif (13 in p_types):
            mu_ind = p_types.index(13)
            p_frame.Put("visible_track", children[mu_ind])
            if not IC_hit:
                pclass = 11 # Passing Track
            elif p_frame['I3MCWeightDict']['InteractionType'] == 3:
                if has_signature(children[mu_ind], surface) == 0:
                    pclass = 8  # Glashow Track
            elif has_signature(children[mu_ind], surface) == 0:
                pclass = 3  # Starting Track
            elif has_signature(children[mu_ind], surface) == 1:
                pclass = 2  # Through Going Track
            elif has_signature(children[mu_ind], surface) == 2:
                pclass = 4  # Stopping Track
        elif (15 in p_types):
            tau_ind = p_types.index(15)
            p_frame.Put("visible_track", children[tau_ind])
            if not IC_hit:
                pclass = 12 # uncontained tau something...
            else:
                # consider to use the interactiontype here...
                if p_frame['I3MCWeightDict']['InteractionType'] == 3:
                    pclass =  9  # Glashow Tau
                else:
                    had_ind = p_strings.index('Hadrons')
                    try:
                        tau_child = I3Tree.children(children[tau_ind])[-1]
                    except:
                        tau_child = None
                    if tau_child:
                        if np.abs(tau_child.pdg_encoding) == 13:
                            if has_signature(tau_child, surface) == 0:
                                pclass = 3  # Starting Track
                            if has_signature(tau_child, surface) == 1:
                                pclass = 2  # Through Going Track
                            if has_signature(tau_child, surface) == 2:
                                pclass = 4  # Stopping Track
                        else:
                            if has_signature(children[tau_ind], surface) == 0 and has_signature(tau_child, surface) == 0:
                                pclass = 5  # Double Bang
                            if has_signature(children[tau_ind], surface) == 0 and has_signature(tau_child, surface) == -1:
                                pclass = 3  # Starting Track
                            if has_signature(children[tau_ind], surface) == 2 and has_signature(tau_child, surface) == 0:
                                pclass = 6  # Stopping Tau
                            if has_signature(children[tau_ind], surface) == 1:
                                pclass = 2  # Through Going Track
                    else: # Tau Decay Length to large, so no childs are simulated
                        if has_signature(children[tau_ind], surface) == 0:
                            pclass = 3 # Starting Track
                        if has_signature(children[tau_ind], surface) == 1:
                            pclass = 2  # Through Going Track
                        if has_signature(children[tau_ind], surface) == 2:
                            pclass = 4  # Stopping Track
        else:
            pclass = 100 # unclassified
    #print('Classification: {}'.format(pclass))
    p_frame.Put("classification", icetray.I3Int(pclass))
    return

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

def track_length_in_detector(frame, gcdfile=None, surface=None,  key="visible_track"):
    if is_data(frame):
        return True
    if surface is None:
        if gcdfile is None:
            surface = icecube.MuonGun.ExtrudedPolygon.from_I3Geometry(frame['I3Geometry'])
        else:
            surface = icecube.MuonGun.ExtrudedPolygon.from_file(gcdfile, padding=0)
    if not key in frame.keys():
        val = 0.
    else:
        p = frame[key]
        intersections = surface.intersection(p.pos, p.dir)
        if frame['classification'].value == 3:
            val = intersections.second # Starting Track
        elif frame['classification'].value == 2:
            val = intersections.second-intersections.first # Through Going Track
        elif frame['classification'].value == 4:
            val = p.length-intersections.first # Stopping Track
        elif frame['classification'].value == 5:
            val = p.length
        elif (frame['classification'].value == 21) | (frame['classification'].value == 22) | (frame['classification'].value == 23):
            val = np.min([p.length-intersections.first,intersections.second-intersections.first])
        else:
            val = 0.
    frame.Put("track_length", dataclasses.I3Double(val))
    return

def classify_wrapper(p_frame, surface, gcdfile=None):
    if is_data(p_frame):
        return True
    if 'I3MCWeightDict' in p_frame.keys():
        classify(p_frame, surface=surface, gcdfile=gcdfile)
        return
    else:
        classify_corsika(p_frame, surface=surface, gcdfile=gcdfile)
        return



#os.listdir()
#argparse
print("directory",sys.argv[1])
list0=os.listdir(sys.argv[1])


def run(i3_file):
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
    #surface = icecube.MuonGun.ExtrudedPolygon.from_file(geo_file, padding=0)
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
    tray.AddModule("I3Reader","source", FilenameList=[i3_file])
    tray.AddModule(classify_wrapper, "classify",surface=None,Streams=[icetray.I3Frame.Physics])
    tray.AddModule(track_length_in_detector, 'track_length', surface=None,Streams=[icetray.I3Frame.Physics])
    tray.AddModule(save_to_array, 'save',Streams=[icetray.I3Frame.Physics])

    print("Saving")
    #save_to_array('track_length')

    tray.Execute()
    tray.Finish()
    print("finish!")

run(list0[0:10])

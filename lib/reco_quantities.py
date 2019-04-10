#!/bin/sh /cvmfs/icecube.opensciencegrid.org/py2-v2/icetray-start
#METAPROJECT /data/user/tglauch/Software/combo/build
# coding: utf-8

"""This file is part of DeepIceLearning
DeepIceLearning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from icecube import dataclasses, dataio, icetray, MuonGun
from icecube.icetray import I3Units
import icecube.MuonGun
import numpy as np
from icecube.weighting.weighting import from_simprod

nu_pdg = [12, 14, 16, -12, -14, -16]

weight_info = {
     '11029': {'nfiles': 3190,'nevents': 200000},
     '11069': {'nfiles': 3920,'nevents': 5000},
     '11070': {'nfiles': 997,'nevents': 400}, }

def calc_gen_ow(frame, gcdfile):
    soft = from_simprod(11029)
    hard_lowE = from_simprod(11069)
    hard_highE = from_simprod(11070)
    generator = 3190 * soft + 3920 * hard_highE + 997 * hard_lowE
    dataset = str(frame['I3EventHeader'].run_id)[0:5]
    ow = 1.*generator(frame['MCPrimary1'].energy, frame['I3MCWeightDict']['PrimaryNeutrinoType'],
                   np.cos(frame['MCPrimary1'].dir.zenith))/weight_info[dataset]['nevents']
    return ow

def calc_depositedE(physics_frame, gcd_file):
    I3Tree = physics_frame['I3MCTree']
    losses = 0
    for p in I3Tree:
        if not p.is_cascade: continue
        if not p.location_type == dataclasses.I3Particle.InIce: continue 
        if p.shape == p.Dark: continue 
        if p.type in [p.Hadrons, p.PiPlus, p.PiMinus, p.NuclInt]:
            if p.energy < 1*I3Units.GeV:
                losses += 0.8*p.energy
            else:
                energyScalingFactor = 1.0 + ((p.energy/I3Units.GeV/0.399)**-0.130)*(0.467 - 1)
                losses += energyScalingFactor*p.energy
        else:
            losses += p.energy 
    return losses

def calc_hitDOMs(physics_frame, gcd_file, which=""):
    IC_hitDOMs = 0
    DC_hitDOMs = 0
    DC = [79, 80, 81, 82, 83, 84, 85, 86]
    pulses = physics_frame["InIceDSTPulses"]
    # apply the pulsemask --> make it an actual mapping of omkeys to pulses
    pulses = pulses.apply(physics_frame)
    for key, pulses in pulses:
        if key[0] in DC:
            DC_hitDOMs +=1
        else:
            IC_hitDOMs +=1
    if which == "IC":
        return IC_hitDOMs
    if which == "DC":
        return DC_hitDOMs



def starting(p_frame, gcdfile):
    I3Tree = p_frame['I3MCTree']
    neutrino = get_the_right_particle(p_frame, gcdfile)
    primary_list = I3Tree.get_primaries()
    surface = icecube.MuonGun.ExtrudedPolygon.from_file(gcdfile, padding=0)
    intersections = surface.intersection(neutrino.pos + neutrino.length * neutrino.dir, neutrino.dir)
    if intersections.first <= 0 and intersections.second > 0:
        starting = 0  # starting event
    else:
        starting = 1  # through-going or stopping event
    return starting


def up_or_down(physics_frame, gcdfile):
    zenith = physics_frame["LineFit"].dir.zenith
    if zenith > 1.5 * np.pi or zenith < 0.5 * np.pi:
        up_or_down = 1  # down-going
    else:
        up_or_down = 0  # up-going
    return up_or_down


def coincidenceLabel_poly(physics_frame, gcdfile):
    poly = physics_frame['PolyplopiaCount']
    #print "Poly {}".format(poly)
    if poly == icetray.I3Int(0):
        coincidence = 0
    #elif poly == icetray.I3Int(0):
    #    coincidence = 0
    else:
        coincidence = 1
    return coincidence

def coincidenceLabel_primary(physics_frame, gcdfile):
    primary_list = physics_frame["I3MCTree"].get_primaries()
    if len(primary_list) > 1:
        coincidence = 1
    else:
        coincidence = 0
    return coincidence


def tau_decay_length(p_frame, gcdfile):
    I3Tree = p_frame['I3MCTree']
    neutrino = get_the_right_particle(p_frame, gcdfile)
    if abs(neutrino.pdg_encoding) == 16:
        return I3Tree.children(neutrino)[0].length
    else:
        return -1


# calculates if the particle is in or near the detector
# if this is the case it further states weather the event is starting,
# stopping or through-going

def has_signature(p, gcdfile):
    surface = MuonGun.ExtrudedPolygon.from_file(gcdfile, padding=0)
    intersections = surface.intersection(p.pos, p.dir)
    if p.is_neutrino:
        return -1
    if not np.isfinite(intersections.first):
        return -1
    if p.is_cascade:
        if intersections.first <= 0 and intersections.second > 0:
            return 0  # starting event
        else:
            return -1  # no hits
    elif p.is_track:
        if intersections.first <= 0 and intersections.second > 0:
            return 0  # starting event
        elif intersections.first > 0 and intersections.second > 0:
            if p.length <= intersections.first:
                return -1  # no hit
            elif p.length > intersections.second:
                return 1  # through-going event
            else:
                return 2  # stopping event
        else:
            return -1


def get_the_right_particle(p_frame, gcdfile):
    I3Tree = p_frame['I3MCTree']
    # find first neutrino as seed for find_particle
    for p in I3Tree.get_primaries():
        if p.pdg_encoding in nu_pdg:
            break
    p_list = find_particle(p, I3Tree, gcdfile)
    if len(p_list) == 0 or len(p_list) > 1:
        return -1
    else:
        return p_list[0]


def testing_event(p_frame, gcdfile):
    I3Tree = p_frame['I3MCTree']
    neutrino = get_the_right_particle(p_frame, gcdfile)
    if neutrino == -1:
        return -1
    else:
        # return 0
        children = I3Tree.children(neutrino)
        p_types = [np.abs(child.pdg_encoding) for child in children]
        p_strings = [child.type_string for child in children]

        if not np.any([p_type in nu_pdg for p_type in p_types]) and not ((11 in p_types) or (13 in p_types) or (15 in p_types)):
            return -1  # kick the event
        else:
            return 0  # everything fine




def find_particle(p, I3Tree, gcdfile):
# returns a list of neutrinos, that children interact with the detector,
# determines after the level, where one is found
    t_list = []
    children = I3Tree.children(p)
    #print "Len Children {}".format(len(children))
    if len(children) > 3:
        return []
    IC_hit = np.any([(has_signature(tp, gcdfile) != -1) for tp in children])
    if IC_hit:
        if p.pdg_encoding not in nu_pdg:
            return [I3Tree.parent(p)]
        else:
            return [p]
    elif len(children) > 0:
        for child in children:
            t_list = np.concatenate([t_list, find_particle(child, I3Tree,
                                                           gcdfile)])
        return t_list
    else:
        return []


# Generation of the Classification Label


def classify(p_frame, gcdfile):
    I3Tree = p_frame['I3MCTree']
    neutrino = get_the_right_particle(p_frame, gcdfile)
    children = I3Tree.children(neutrino)
    p_types = [np.abs(child.pdg_encoding) for child in children]
    p_strings = [child.type_string for child in children]

    if p_frame['I3MCWeightDict']['InteractionType'] == 3 and (len(p_types) == 1 and p_strings[0] == 'Hadrons'):
        return 7  # Glashow Cascade
    if np.any([p_type in nu_pdg for p_type in p_types]) and not (p_frame['I3MCWeightDict']['InteractionType'] == 3):
        return 0  # is NC event
    else:
        if (11 in p_types):
            return 1  # Cascade
        if (13 in p_types):
            mu_ind = p_types.index(13)
            if 'Hadrons' not in p_strings:
                if has_signature(children[mu_ind], gcdfile) == 0:
                    return 8  # Glashow Track
            if has_signature(children[mu_ind], gcdfile) == 0:
                return 3  # Starting Track
            if has_signature(children[mu_ind], gcdfile) == 1:
                return 2  # Through Going Track
            if has_signature(children[mu_ind], gcdfile) == 2:
                return 4  # Stopping Track
        if (15 in p_types):
            tau_ind = p_types.index(15)
            # consider to use the interactiontype here...
            if 'Hadrons' not in p_strings:
                return 9  # Glashow Tau
            had_ind = p_strings.index('Hadrons')
            try:
                tau_child = I3Tree.children(children[tau_ind])[-1]
            except:
                tau_child = None
            if tau_child:
                if np.abs(tau_child.pdg_encoding) == 13:
                    if has_signature(tau_child, gcdfile) == 0:
                        return 3  # Starting Track
                    if has_signature(tau_child, gcdfile) == 1:
                        return 2  # Through Going Track
                    if has_signature(tau_child, gcdfile) == 2:
                        return 4  # Stopping Track
                else:
                    if has_signature(children[tau_ind], gcdfile) == 0 and has_signature(tau_child, gcdfile) == 0:
                        return 5  # Double Bang
                    if has_signature(children[tau_ind], gcdfile) == 0 and has_signature(tau_child, gcdfile) == -1:
                        return 3  # Starting Track
                    if has_signature(children[tau_ind], gcdfile) == -1 and has_signature(tau_child, gcdfile) == 0:
                        return 6  # Stopping Tau
            else: # Tau Decay Length to large, so no childs are simulated
                if has_signature(children[tau_ind], gcdfile) == 0:
                    return 3 # Starting Track
                if has_signature(children[tau_ind], gcdfile) == 1:
                    return 2  # Through Going Track
                if has_signature(children[tau_ind], gcdfile) == 2:
                    return 4  # Stopping Track

def track_length_in_detector(p_frame, gcdfile):
    I3Tree = p_frame['I3MCTree']
    neutrino = get_the_right_particle(p_frame, gcdfile)
    children = I3Tree.children(neutrino)
    p_types = [np.abs(child.pdg_encoding) for child in children]
    p_strings = [child.type_string for child in children]
    surface = MuonGun.ExtrudedPolygon.from_file(gcdfile, padding=0)
    classify_result = classify(p_frame, gcdfile)
    
    if classify_result in [0, 1, 5, 7]: #NC event, Cascade, Double Bang, Glashow Cascade  -> no track length
        return -1
        
    if (13 in p_types):
        mu_ind = p_types.index(13)
#################################################################################
        if 'Hadrons' not in p_strings:
            if has_signature(children[mu_ind], gcdfile) == 0: # 0=Starting #??????????????????
                return -1  # Glashow Track
#################################################################################
        p = children[mu_ind]
        intersections = surface.intersection(p.pos, p.dir)  
        if has_signature(children[mu_ind], gcdfile) == 0:
            return intersections.second # Starting Track
        if has_signature(children[mu_ind], gcdfile) == 1:
            return intersections.second-intersections.first # Through Going Track 
        if has_signature(children[mu_ind], gcdfile) == 2:
            return p.length-intersections.first # Stopping Track
    if (15 in p_types):
        tau_ind = p_types.index(15)
#################################################################################
        # consider to use the interactiontype here...
        if 'Hadrons' not in p_strings:
            return -1  # Glashow Tau
#################################################################################
        had_ind = p_strings.index('Hadrons')
        try:
            tau_child = I3Tree.children(children[tau_ind])[-1]
        except:
            tau_child = None
        if tau_child:
            p = tau_child
            intersections = surface.intersection(p.pos, p.dir)
            if has_signature(tau_child, gcdfile) == 0:
                return intersections.second # Starting Track
            if has_signature(tau_child, gcdfile) == 1:
                return intersections.second-intersections.first # Through Going Track
            if has_signature(tau_child, gcdfile) == 2:
                return p.length-intersections.first # Stopping Track, Stopping Tau        
        else: # Tau Decay Length to large, so no childs are simulated
            p = children[tau_ind]
            intersections = surface.intersection(p.pos, p.dir)
            if has_signature(children[tau_ind], gcdfile) == 0:
                return intersections.second # Starting Track
            if has_signature(children[tau_ind], gcdfile) == 1:
                return intersections.second-intersections.first # Through Going Track
            if has_signature(children[tau_ind], gcdfile) == 2:
                return p.length-intersections.first # Stopping Track

def time_of_percentage(charges, times, percentage):
    charges = charges.tolist()
    cut = np.sum(charges) / (100. / percentage)
    sum = 0
    for i in charges:
        sum = sum + i
        if sum > cut:
            tim = times[charges.index(i)]
            break
    return tim


# calculate a quantile
# based on the waveform
def wf_quantiles(wfs, quantile, srcs=['ATWD', 'FADC']):
    ret = dict()
    src_loc = [wf.source.name for wf in wfs]
    for src in srcs:
        ret[src] = 0
        if src not in src_loc:
            continue
        wf = wfs[src_loc.index(src)]
        t = wf.time + np.linspace(0, len(wf.waveform) * wf.bin_width, len(wf.waveform))
        charge_pdf = np.cumsum(wf.waveform) / np.cumsum(wf.waveform)[-1]
        ret[src] = t[np.where(charge_pdf > quantile)[0][0]]
    return ret

#based on the pulses
def pulses_quantiles(charges, times, quantile):
    tot_charge = np.sum(charges)    
    cut = tot_charge*quantile
    progress = 0
    for i, charge in enumerate(charges):
        progress += charge
        if progress >= cut:
            return times[i]


def get_dir(p_frame, gcdfile, which=""):
    neutrino = get_the_right_particle(p_frame, gcdfile)
    if which == "x":
        return neutrino.dir.x
    if which == "y":
        return neutrino.dir.y
    if which == "z":
        return neutrino.dir.z

def get_inelasticity(p_frame, gcdfile):
    I3Tree = p_frame['I3MCTree']
    interaction_type = p_frame['I3MCWeightDict']['InteractionType']
    if interaction_type!= 1:
        return 0
    else:
        neutrino = get_the_right_particle(p_frame, gcdfile)
        children = I3Tree.children(neutrino)
        for child in children:
            if child.type_string == "Hadrons":
                return 1.0*child.energy/neutrino.energy 

def get_vertex(p_frame, gcdfile, which=""):
    I3Tree = p_frame['I3MCTree']
    neutrino = get_the_right_particle(p_frame, gcdfile)
    if which == "x":
        return I3Tree.children(neutrino)[0].pos.x
    if which == "y":
        return I3Tree.children(neutrino)[0].pos.y    
    if which == "z":
        return I3Tree.children(neutrino)[0].pos.z

def millipede_rel_highest_loss(frame, gcdfile):
    e_losses = [i.energy for i in frame['SplineMPE_MillipedeHighEnergyMIE'] if i.energy > 0.]
    if len(e_losses) == 0:
        return 0
    return np.max(e_losses) / np.sum(e_losses)


def millipede_n_losses(frame, gcdfile):
    e_losses = [i.energy for i in frame['SplineMPE_MillipedeHighEnergyMIE'] if i.energy > 0.]
    return len(e_losses)


def millipede_std(frame, gcdfile):
    e_losses = [i.energy for i in frame['SplineMPE_MillipedeHighEnergyMIE'] if i.energy>0.]
    if len(e_losses) == 0:
        return 0
    return np.std(e_losses)/np.mean(e_losses)


def millipede_max_loss(frame, gcdfile):
    e_losses = [i.energy for i in frame['SplineMPE_MillipedeHighEnergyMIE'] if i.energy>0.]
    if len(e_losses) == 0:
        return 0
    return np.amax(e_losses)


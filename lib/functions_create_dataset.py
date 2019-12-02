
import logging
import numpy as np
#import icecube.MuonGun
#from icecube import dataclasses, dataio, simclasses
import scipy.stats as st

def get_t0(frame, puls_key='InIceDSTPulses'):
    pulses = frame[puls_key]
    pul = pulses.apply(frame)
    time = []
    charge = []
    for i in pul:
        for j in i[1]:
            charge.append(j.charge)
            time.append(j.time)
    return median(time, weights=charge)


def median(arr, weights=None):
    if weights is not None:
        weights = 1. * np.array(weights)
    else:
        weights = np.ones(len(arr))
    rv = st.rv_discrete(values=(arr, weights / weights.sum()))
    return rv.median()


def read_variables(cfg_parser):
    """Function reading a config file, defining the variables to be read
       from the MC files.

    Arguments:
    cfg_parser: config parser object for the config file

    Returns:
    dtype : the dtype object defining the shape and names of the MC output
    data_source: list defining the types,names and ranges of monte carlo data
                to be saved from a physics frame
                (e.g [('variable',['MCMostEnergeticTrack'].energy, [1e2,1e9])])
    """
    dtype = []
    data_source = []
    cut = [-np.inf, np.inf]
    for i in cfg_parser['Variables'].keys():
        data_source.append(('variable', cfg_parser['Variables'][i], cut))
        dtype.append((str(i), np.float64))
    for i in cfg_parser['Functions'].keys():
        data_source.append(('function', cfg_parser['Functions'][i]+'(_icframe_)', cut))
        dtype.append((str(i), np.float64))
    dtype = np.dtype(dtype)
    return dtype, data_source


def charge_after_time(charges, times, t=100):
    mask = (times - np.min(times)) < t
    return np.sum(charges[mask])


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
    return 0
#    ret = dict()
#    src_loc = [wf.source.name for wf in wfs]
#    for src in srcs:
#        ret[src] = 0
#        if src not in src_loc:
#            continue
#        wf = wfs[src_loc.index(src)]
#        t = wf.time + np.linspace(0, len(wf.waveform) * wf.bin_width, len(wf.waveform))
#        charge_pdf = np.cumsum(wf.waveform) / np.cumsum(wf.waveform)[-1]
#        ret[src] = t[np.where(charge_pdf > quantile)[0][0]]

#based on the pulses
def pulses_quantiles(charges, times, quantile):
    tot_charge = np.sum(charges)
    cut = tot_charge*quantile
    progress = 0
    for i, charge in enumerate(charges):
        progress += charge
        if progress >= cut:
            return times[i]


def nmoment(x, counts, c, n):
    return np.sum(counts*(x-c)**n) / np.sum(counts)


def normalize(time,charge):

    charge=charge[time[:]<=time[0]+400]
    time=time[time[:]<=time[0]+400]

    t=max(time-min(time))
    #np.seterr(divide='ignore', invalid='ignore')
    if(t==t and t!=0):
        #print(max(time-min(time)))
        return (time-min(time))/max(time-min(time))
    else:
        return time, charge


def mean(charge,time):
    time=normalize(time)
    return nmoment(time,charge, 0,1)

def var(charge,time):
    return nmoment(time,charge, 0,2)

def skw(charge,time):
    return nmoment(time,charge, 0,3)

def kur(charge,time):
    return nmoment(time,charge, 0,4)

def mult(charge,time):
    if (len(time)<4):
        return 0
    else:
        time , charge = normalize(time,charge)
        kur1=kur(charge,time)

        if(kur1==kur1 and kur1!=0):
            kur2=(skw(charge,time)**2+1)/kur1
            if(kur2 != kur2):
    	           return 0
    	else:
    	    return kur2

def diff(charge,time):
    if (len(time)<4):
        return 0
    else:

        time , charge = normalize(time,charge)
        diff1= mean(charge,time)-time[np.argmax(charge)]

        if (diff1 != diff1):
            return 0
        else:
            return diff1

##



# python create_data_files.py --dataset_config /data/user/pruiz/DeepIceLearning/configs/create_dataset_all_flav_w_corsika.cfg --files /data/ana/Cscd/StartingEvents/NuGen_new/NuTau/medium_energy/IC86_flasher_p1\=0.3_p2\=0.0/l2/1/l2_00000111.i3.zst

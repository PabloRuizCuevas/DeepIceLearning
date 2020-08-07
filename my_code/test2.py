from icecube import dataio,dataclasses,phys_services
import pandas as pd
import numpy as np
import os
import imp
DeepIce = imp.load_source('DeepIce', '/data/user/pruiz/DeepIceLearning/lib/reco_quantities.py')

def count_physics_frames(f):
    count=0
    f.rewind()

    while f.more() == True:
        if str(f.stream)=='Physics':
            count+=1
        fr = f.pop_frame()

    if str(f.stream)=='Physics':
        count+=1

    f.rewind()
    return count

def calc_time_charge(pulsemap):
    charge,time,width,flag=[],[],[],[]

    for i in range(len(pulsemap)):
        charge.append(pulsemap[i].charge)
        time.append(pulsemap[i].time)
        width.append(pulsemap[i].width)
        flag.append(pulsemap[i].flags)

    return charge,time,width,flag  #np.array(charge),np.array(time),np.array(width),np.array(flag)

def charge_time_most_recorded_dom(fr,n):

    offline_pulses = fr["SplitInIcePulses"]   #["split_INI"]    #["InIcePulses"] worked for mc "SplitInIcePulses"   ##[]"OfflinePulsesHLC"]    #no idea which one
    if type(offline_pulses) == dataclasses.I3RecoPulseSeriesMapMask:
        offline_pulses = offline_pulses.apply(fr)

    records=[]
    for i in range(len(offline_pulses)):
        records.append(len(offline_pulses[offline_pulses.keys()[i]]))
    records=np.array(records)

    key=np.argsort(records)[-n]   ## posiion of the most recorded dom
    pulsemap=offline_pulses[offline_pulses.keys()[key]]
    data=calc_time_charge(pulsemap)

    return data


directory="/data/user/pruiz/DeepIceLearning/IC86_2014" #"/data/user/pruiz/i3/data/5"

ndoms=20
col=["charge","time","width","flag","filename"]
df = pd.DataFrame(columns=col)
frames=0
count=0
for filename in os.listdir(directory):
    if filename.endswith(".bz2"): 
	print("filename:",filename)
        f = dataio.I3File(os.path.join(directory, filename))
        f.rewind()
        physics_frames=count_physics_frames(f)
        for i in range(physics_frames):
            fr = f.pop_physics()  
        
	    for n in range(1,ndoms):
                data=np.array(charge_time_most_recorded_dom(fr,n))
                row=np.array([data[0],data[1],data[2],data[3],filename])
                df.loc[count]=row
                count+=1
            else:
                continue

path="/data/user/pruiz/DeepIceLearning/notebooks/double_bang_real"
#two ways to save and load
df.to_pickle(path)  # where to save it, usually as a .pkl
print("dataframe saved in", path)


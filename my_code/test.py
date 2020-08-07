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

    offline_pulses = fr["InIcePulses"]       #["InIcePulses"] "SplitInIcePulses"   ##[]"OfflinePulsesHLC"]    #no idea which one
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

gdfile="/data/user/pruiz/i3/GeoCalibDetectorStatus_2013.56429_V0.i3.gz"

nfiles=20
ndoms=20

col=["charge","time","width","flag","class","lenght","frame"]
df = pd.DataFrame(columns=col)
frames=0
count=0
for filename in os.listdir(directory)[0:nfiles]:
    if filename.endswith(".i3"): 
        #DeepIce.classify(fr,gdfile)
        f = dataio.I3File(os.path.join(directory, filename))
        f.rewind()
        physics_frames=count_physics_frames(f)
        for i in range(physics_frames):
            fr = f.pop_physics()
            DeepIce.classify(fr,gdfile)
            classi=fr["classification"].value    
            if classi in {1,5}:
                frames+=1
		DeepIce.track_length_in_detector(fr,gdfile, surface=None,  key="visible_track")
		for n in range(1,ndoms):
		    
                    data=np.array(charge_time_most_recorded_dom(fr,n))
                    row=np.array([data[0],data[1],data[2],data[3],classi,fr["track_length"].value,frames])
                    df.loc[count]=row
                    count+=1
            else:
                continue

path="/data/user/pruiz/DeepIceLearning/notebooks/pdframe_dataDoms"
#two ways to save and load
df.to_pickle(path)  # where to save it, usually as a .pkl
df = pd.read_pickle(file_name)

store = HDFStore('store.h5')
store['df'] = df  # save it
store['df']  # load it


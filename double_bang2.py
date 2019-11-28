
from icecube import dataio,dataclasses,phys_services
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

def charge_density(charge,time):
    dif=[]
    density=[]
    time2=[]
    for i in range(len(time)-2):
        dif.append(time[i+1]-time[i])
        time2.append(time[i+1])
        density.append(charge[i+1]/dif[i])
    return time2,density



class Data:
  def __init__(self,n, charge, time,width,flag,classification,track_length,physics_frame):
    self.event = n
    self.charge,self.time,self.width,self.flag = np.array(charge),np.array(time),np.array(width),np.array(flag)
    self.classification = classification
    self.track_length = track_length
    self.physics_frame = physics_frame




directory="/data/user/pruiz/i3/data/5"
gdfile="/data/user/pruiz/i3/GeoCalibDetectorStatus_2013.56429_V0.i3.gz"
def get_frame_info(directory,gdfile):

    frames=[]
    count=0
    for filename in os.listdir(directory):
        if (filename.endswith(".i3") and count<1000):              #load all the i3 files in directory
            print(count)
            f = dataio.I3File(os.path.join(directory, filename))   #open one
            f.rewind()
            physics_frames=count_physics_frames(f)
            #print(physics_frames)
            for i in range(physics_frames):

                fr = f.pop_physics()
                data=charge_time_most_recorded_dom(fr,1)             ##salen datos repetidos por parejas???
                DeepIce.classify(fr,gdfile)
                DeepIce.track_length_in_detector(fr,gdfile, surface=None,  key="visible_track")
                frames.append(Data(count,data[0],data[1],data[2],data[3],fr["classification"].value,fr["track_length"].value,i))

            count+=1
    np.save("frames",frames)
    return frames

frames=get_frame_info(directory,gdfile)



directory="/data/user/pruiz/i3/data/5"
gdfile="/data/user/pruiz/i3/GeoCalibDetectorStatus_2013.56429_V0.i3.gz"
def get_frame_info2(directory,gdfile,N):

    frames=[]
    count=0
    for filename in os.listdir(directory):
        if (filename.endswith(".i3") and count<1000):              #load all the i3 files in directory
            print(count)
            f = dataio.I3File(os.path.join(directory, filename))   #open one
            f.rewind()
            physics_frames=count_physics_frames(f)
            #print(physics_frames)
            for i in range(physics_frames):
                fr = f.pop_physics()
                DeepIce.classify(fr,gdfile)
                #if fr["classification"] == 5:
                DeepIce.track_length_in_detector(fr,gdfile, surface=None,  key="visible_track")
                for n in range(N):
                    data=charge_time_most_recorded_dom(fr,n)             ##salen datos repetidos por parejas???
                    frames.append(Data(count,data[0],data[1],data[2],data[3],fr["classification"].value,fr["track_length"].value,i))

            count+=1
    np.save("frames2",frames)
    return frames
frames2=get_frame_info2(directory,gdfile,10)
#in my machine
#scp "pruiz@cobalt.icecube.wisc.edu:/data/user/pruiz/frames.npy" "/home/pablo/Documents/Master/Icecube/my_code"

#count_physics_frames(dataio.I3File("i3/data/126283.i3"))

DeepIce.track_length_in_detector(fr,"/data/user/pruiz/i3/GeoCalibDetectorStatus_2013.56429_V0.i3.gz", surface=None,  key="visible_track")




#####################################plot data##################################
import matplotlib.pyplot as plt
import numpy as np

class Data:
  def __init__(self,n, charge, time,width,flag,classification,track_length,physics_frame):
    self.event = n
    self.charge,self.time,self.width,self.flag = np.array(charge),np.array(time),np.array(width),np.array(flag)
    self.classification = classification
    self.track_length = track_length
    self.physics_frame = physics_frame


frames0=np.load('/home/pablo/Documents/Master/Icecube/my_code/frames2.npy')
frames0=frames0[[ 2*i for i in range(len(frames0)/2)]]   ##destros half of the data repeated data???




def nmoment(x, counts, c, n):
    return np.sum(counts*(x-c)**n) / np.sum(counts)


class Frame_array:
    def __init__(self,frames):
        #print(len(frames))
        if np.size(frames)>1:
            for i in range(np.size(frames)):
                frames[i].time_normalized=(frames[i].time-min(frames[i].time))/max(frames[i].time-min(frames[i].time))  #not best efficiency
                frames[i].mean=nmoment(frames[i].time_normalized,frames[i].charge, 0,1)
                frames[i].var=nmoment(frames[i].time_normalized,frames[i].charge, 0,2)
                frames[i].skw=nmoment(frames[i].time_normalized,frames[i].charge, 0,3)
                frames[i].kur=nmoment(frames[i].time_normalized,frames[i].charge, 0,4)
                frames[i].mult=(frames[i].skw**2+1)/frames[i].kur
                frames[i].dif=frames[i].mean-frames[i].time_normalized[np.argmax(frames[i].charge)]
                frames[i].len=len(frames[i].charge)

            self.mean =np.array([ frames[i].mean for i in range(len(frames))])
            self.var =np.array([ frames[i].var for i in range(len(frames))])
            self.skw =np.array([ frames[i].skw for i in range(len(frames))])
            self.kur =np.array([ frames[i].kur for i in range(len(frames))])
            self.mult =np.array([ frames[i].mult for i in range(len(frames))])
            self.dif= np.array([ frames[i].dif for i in range(len(frames))])
            self.len= np.array([ frames[i].len for i in range(len(frames))])
            self.track_length=np.array([ frames[i].track_length for i in range(len(frames))])
            self.classification=np.array([ frames[i].classification for i in range(len(frames))])
            self.size=np.size(self.mean )


        if np.size(frames)==1:
            self.charge = frames.charge
            self.time = frames.time
            self.width= frames.width
            self.flag= frames.width
            self.track_length=frames.track_length
            self.classification=frames.classification
            self.time_normalized=(self.time-min(self.time))/max(self.time-min(self.time))
            self.mean=nmoment(self.time_normalized,self.charge, 0,1)
            self.var=nmoment(self.time_normalized,self.charge, 0,2)
            self.skw=nmoment(self.time_normalized,self.charge, 0,3)
            self.kur=nmoment(self.time_normalized,self.charge, 0,4)
            self.mult=(self.skw**2+1)/self.kur
            self.dif= self.mean-self.time_normalized[np.argmax(self.charge)]
            self.len=np.size(self.charge)
            self.size=1
            #print("catastrofe")
        if np.size(frames)==0:
            self.charge,self.time,self.width,self.flag,self.track_length,self.classification,self.time_normalized=[],[],[],[],[],[],[]
            self.mean,self.var,self.skw,self.kur,self.mult,self.dif,self.len=[],[],[],[],[],[],[]
            self.size=0

            print("No events")

    def __getitem__(self,indx):
        #
        #Frame_array(frames0[indx])
        return Frame_array(frames0[indx])   ##ahora entinedo poq dos condiciones no se anidan bn siempre se refieren a frames0 no al nuevo subconjunto

frames=Frame_array(frames0)


#frames[np.logical_and(frames.classification==5,frames.len>50 )].size
#frames[np.array(frames.classification==5) & np.array(frames.len>50 ) ].size
#frames[np.equal(frames.classification,5) & np.equal(frames.len,50 ) ].size

#########################################################################


def plot1(x,y,y2,a):
    plt.subplot(2, 1, 1)
    plt.scatter(x,y,c=a,alpha=0.3)
    plt.xlabel('mult', fontsize=18)
    plt.ylabel('dif', fontsize=16)
    plt.subplot(2, 1, 2)
    plt.scatter(x,y2,c=a,alpha=0.3)
    plt.xlabel('mult', fontsize=18)
    plt.ylabel('var', fontsize=16)
    plt.show()

x=frames.mult
y=frames.dif
y2=frames.var
c=frames.classification
a=np.array(c)
a[a!=5]=0
a[a==5]=1



plot1(x,y,y2,a)

a=np.array(frames.classification==5)
x=frames[a].mult
y=frames[a].dif
y2=frames[a].var
a=frames[a].classification

plot1(x,y,y2,a)

a=np.array(frames.classification==5)
b=np.array(frames.track_length>10)
c=np.array(frames.len>60)
d=np.array(frames.track_length<100)
a&b&c

frames[a&b&c&d].size

x=frames[a&b&c&d].mult
y=frames[a&b&c&d].dif
y2=frames[a&b&c&d].var
cl=frames[a&b&c&d].classification

plot1(x,y,y2,cl)

frames[a&b&c].size
i=np.where(a&b&c)[0][np.int(np.floor(np.random.uniform(490)))]

plt.scatter(frames[i].time,frames[i].charge,c=frames[i].flag)
plt.xlim(min(frames[i].time), min(frames[i].time)+2000)
frames[i].track_length/3e8*1.3*1e9



frames[10].charge
############################################################################

frames[frames.classification==5].len


a=frames[frames.classification==5].track_length>10

i=np.argsort(x)[1]


frames[frames.len>50].size



plt.scatter(x2,y2,alpha=0.3)

np.array(frames.classification==5) & np.array(frames.classification==5)



n=12
multi=np.argsort(x2)
plt.subplot(2, 1, 1)
i=multi[n]
x=frames[frames.classification==5][i].time
y=frames[frames.classification==5][i].charge
plt.scatter(x,y,alpha=0.3)
plt.subplot(2, 1, 2)
i=multi[-n]
x=frames[frames.classification==5][i].time
y=frames[frames.classification==5][i].charge
plt.scatter(x,y,alpha=0.3)








plt.scatter(mean,dif,s=track_length,alpha=0.5)
plt.show()


i=np.argsort(var)[-1]

i=np.argsort(track_length)[-20]
track_length[i]
track_length[i]/3e8*1e9*1.31
#17/3e8*1e9*1.31
#1/1.31
len(track_length)
t=np.argmax(frames2[i].charge)
second=frames2[i].time[t]+track_length[i]/3e8*1e9*1.31
second

plt.scatter(frames2[i].time_normalized,frames2[i].charge)

plt.plot([second,second],[20,-1])
#plt.xlim(9500, 11000)



def normalize():
    data_double_charge[0]/sum(data_double_charge[0])

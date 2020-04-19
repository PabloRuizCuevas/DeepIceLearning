
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


def charge_time_most_recorded_dom(fr):

    offline_pulses = fr["InIcePulses"]       #["InIcePulses"] "SplitInIcePulses"   ##[]"OfflinePulsesHLC"]    #no idea which one
    if type(offline_pulses) == dataclasses.I3RecoPulseSeriesMapMask:
        offline_pulses = offline_pulses.apply(fr)

    records=[]
    for i in range(len(offline_pulses)):
        records.append(len(offline_pulses[offline_pulses.keys()[i]]))
    records=np.array(records)

    key=np.argsort(records)[-1]   ## posiion of the most recorded dom
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
  def __init__(self,n, charge, time,width,flag):
    self.event,self.charge,self.time,self.width,self.flag =  n,charge, time,width,flag



frame=[]
frame.append(Data(1,np.array([1,2,3,4,5]),2,3,4))
frame.append(Data(2,np.array([1,2,3,4,5]),2,3,4))





directory="/data/user/pruiz/i3/data/5"
data_double,data_single=[],[]
count=0
for filename in os.listdir(directory):
    if (filename.endswith(".i3") and count<1000):              #load all the i3 files in directory
        print(count)
        f = dataio.I3File(os.path.join(directory, filename))   #open one
        f.rewind()
        physics_frames=count_physics_frames(f)
        #print(physics_frames)
        for i in range(physics_frames):
            #print(i)
            #print(filename)
            fr = f.pop_physics()
            data=charge_time_most_recorded_dom(fr)   ##salen datos repetidos por parejas???
            #print(data[0][0])
            DeepIce.classify(fr,"/data/user/pruiz/i3/GeoCalibDetectorStatus_2013.56429_V0.i3.gz")

            #print(fr["classification"])
            if (fr["classification"]==5):
                #print("bang bang")
                data_double.append(data)
            else:
                #print("bang")
                data_single.append(data)

        count+=1
        continue
    else:
        continue

np.save("data_double",data_double)
np.save("data_single",data_single)


#count_physics_frames(dataio.I3File("i3/data/126283.i3"))





#####################################plot data################################



data_double=np.load('/home/pablo/Documents/Master/Icecube/my_code/data_double.npy')
data_single=np.load('/home/pablo/Documents/Master/Icecube/my_code/data_single.npy')



def plots(data_double,data_single):

    data_double_charge=np.array([np.array(xi) for xi in data_double[:,0]])
    data_double_time=np.array([np.array(xi) for xi in data_double[:,1]])
    data_double_width=np.array([np.array(xi) for xi in data_double[:,2]])
    data_double_flag=np.array([np.array(xi) for xi in data_double[:,3]])

    data_single_charge=np.array([np.array(xi) for xi in data_single[:,0]])
    data_single_time=np.array([np.array(xi) for xi in data_single[:,1]])
    data_single_width=np.array([np.array(xi) for xi in data_single[:,2]])
    data_single_flag=np.array([np.array(xi) for xi in data_single[:,3]])


    est1,est2,var_double,kur_double,var,kur,skw,skw_double,B,B_double=[],[],[],[],[],[],[],[],[],[]
    #flag=7
    n=1000
    N1=len(data_single_charge)
    for i in range(N1):
        single_density=data_single_charge[i]/data_single_width[i]
        single_time=data_single_time[i]

        data_single_flag



        #single_density=single_density[data_single_flag[i]==flag]
        #single_time=single_time[data_single_flag[i]==flag]

        single_density=single_density[0:n]
        single_time=single_time[0:n]

        est1.append(np.abs(single_density[np.argmax(single_density)]- np.average(single_time, weights=single_density)))   #diferencia entre max y average

        var.append(nmoment(single_time,single_density, 0,2))
        skw.append(nmoment(single_time,single_density, 0,3))
        kur.append(nmoment(single_time,single_density, 0,4))
        B.append((skw[i]**2+1)/kur[i])


    N2=len(data_double_charge)
    for i in range(N2):
        double_density=data_double_charge[i]/data_double_width[i]
        double_time=data_double_time[i]

        #double_density=double_density[data_double_flag[i]==flag]
        #double_time=double_time[data_double_flag[i]==flag]

        #print(len(double_density))
        double_density=double_density[0:n]
        double_time=double_time[0:n]

        #out1=~is_outlier(data_double_time[i],outl)
        #data_double_charge[i]= data_double_charge[i][out1] ######not really good just for plot faster
        #data_double_time[i] = data_double_time[i][out1]
        #average = np.average(time, weights=charge)
        est2.append(np.abs(double_density[np.argmax(double_density)]- np.average(double_time, weights=double_density)))#diferencia entre max y average

        var_double.append(nmoment(double_time,double_density, 0,2))
        skw_double.append(nmoment(double_time,double_density, 0,3))
        kur_double.append(nmoment(double_time,double_density, 0,4))

        B_double.append((skw_double[i]**2+1)/kur_double[i])

    plt.scatter(np.log10(B),np.log10(est1),alpha=0.2)
    plt.scatter(np.log10(B_double),np.log10(est2),alpha=0.2)
    plt.savefig("Double_bang_separation.png")
    plt.show()
    #plt.scatter(np.log10(skw),np.log10(var))
    #plt.scatter(np.log10(skw_double),np.log10(var_double))



#outl=10
plots(data_double,data_single)

plt.savefig("Double_bang_separation.png")



i=46
data=data_double_charge[i]
datatime=data_double_time[i]
plt.plot(data)
plt.plot(datatime,data)
plt.xlim(9500, 14000)



maximun=np.argwhere(data==max(data))
data[maximun]

np.argwhere( data>400)


and data>(data[maximun]+2000) ))

and data_double_time[0]<(data_double_time[0][maximun]+2000)

data_double_charge[0][3]

def normalize():
    data_double_charge[0]/sum(data_double_charge[0])

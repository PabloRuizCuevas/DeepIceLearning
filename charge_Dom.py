from icecube import dataio,dataclasses,phys_services
import numpy as np


##################charge collected and time in the dom with most records#################

from icecube import dataio,dataclasses,phys_services
import numpy as np


dir="i3/data/126283.i3"
n=1  #the most recorded 2 the second etc



def most_recorded_pulse_data(dir,n):

    f = dataio.I3File(dir)
    fr = f.pop_physics()
    offline_pulses = fr["OfflinePulsesHLC"]

    if type(offline_pulses) == dataclasses.I3RecoPulseSeriesMapMask:
            offline_pulses = offline_pulses.apply(fr)

    records=[]
    for i in range(len(offline_pulses)):
        records.append(len(offline_pulses[offline_pulses.keys()[i]]))
    records=np.array(records)

    def calc_time_charge(pulsemap):
        charge,time,width,flag=[],[],[],[]

        for i in range(len(pulsemap)):
            charge.append(pulsemap[i].charge)
            time.append(pulsemap[i].time)
            width.append(pulsemap[i].width)
            flag.append(pulsemap[i].flags)

        return np.array(charge),np.array(time),np.array(width),np.array(flag)

    #np.argwhere(records>160)   ##see which one do you want and select the key (the most recorded for example)
    key=np.argsort(records)[-n]
    #key=83

    pulsemap=offline_pulses[offline_pulses.keys()[key]]
    data=calc_time_charge(pulsemap)
    np.save("data_{}".format(key),data)
    return data




#########################data only one dom####################################



#only the most recorded domm
import matplotlib.pyplot as plt
from scipy import optimize

key=83
charge=np.load('/home/pablo/Documents/Master/Icecube/my_code/data_{}.npy'.format(key))[0]
time=np.load('/home/pablo/Documents/Master/Icecube/my_code/data_{}.npy'.format(key))[1]
width=np.load('/home/pablo/Documents/Master/Icecube/my_code/data_{}.npy'.format(key))[2]
flag=np.load('/home/pablo/Documents/Master/Icecube/my_code/data_{}.npy'.format(key))[3]
charge_density=charge/width

#flags  7,3,5


charge7=charge[flag==7]
time7=time[flag==7]
width7=width[flag==7]
density7=charge7/width7

charge5=charge[flag==5]
time5=time[flag==5]
width5=width[flag==5]
density5=charge5/width5

charge3=charge[flag==3]
time3=time[flag==3]
width3=width[flag==3]
density3=charge3/width3

plot(time7,density7)
plot(time5,density5)
plot(time3,density3)
plt.savefig("Double_bang4.png")

def plot(x,y):
    plt.scatter(x,y)
    plt.xlim(9800, 10600)
    plt.title('Double bang event')
    plt.xlabel("time ns")
    plt.ylabel("charge")
    plt.savefig("Double_bang4.png")


plot(time,charge)
plot(time,charge_density)


bins = np.linspace(9800,10600,36)
plt.hist(time, weights=charge_density,bins=bins)
#plt.xlim(9800, 11000)
plt.show()


def charge_density(charge,time):
    dif=[]
    density=[]
    time2=[]
    for i in range(len(time)-2):
        dif.append(time[i+1]-time[i])
        time2.append(time[i+1])
        density.append(charge[i+1]/dif[i])
    return time2,density

time2,density=charge_density(charge,time)

plot(time2,density)


bins = np.linspace(9800,10600,29)
plt.hist(time2, weights=density,bins=bins)
plt.savefig("Double_bang4.png")
#plt.xlim(9800, 11000)
plt.show()


time2
density

plt.scatter(time,charge_density)
plt.plot(time,np.gradient(charge_density))
plt.xlim(9800, 10600)




###ideas, gradiente y gradiente con los datos averageados un poco
#idea segunda derivada positiva y gradiente positivo
#

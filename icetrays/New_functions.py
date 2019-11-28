#function features f(time,charge)

def nmoment(x, counts, c, n):
    return np.sum(counts*(x-c)**n) / np.sum(counts)

def normalize(time):
    return (time-min(time))/max(time-min(time))

def mean(charge,time):
    return nmoment(time,charge, 0,1)

def var(charge,time):
    return nmoment(time,charge, 0,2)

def skw(charge,time):
    return nmoment(time,charge, 0,3)

def kur(charge,time):
    return nmoment(time,charge, 0,4)

def mult(charge,time):
    return (skw(charge,time)**2+1)/kur(charge,time)

def diff(charge,time):
    return mean(charge,time)-time[argmax(cahrge)]

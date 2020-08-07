import numpy as np
import h5py
import os
import sys

#directory="/home/pablo/github/DeepIceLearning/h5_final3"  # "h5_no_filter"      #final2 and final3 have the same athimut distribut among double and cascades
directory = sys.argv[1]

it=0
classi=np.array([])
for filename in os.listdir(directory):
    it=it+1
    if filename.endswith(".h5") and it <100000: 
        path=os.path.join(directory, filename)
        File=h5py.File(path,'r')
        classi=np.append(classi,File["reco_vals"]["classification"])
        
db=sum(classi==5)
cascades=sum(classi==1)
print("Number of double bang events in the directory",db,":",np.round(100*db/(db+cascades),1),"%") 
print("Number of Cascades events in the directory",cascades,":",np.round(100*cascades/(db+cascades),1),"%")


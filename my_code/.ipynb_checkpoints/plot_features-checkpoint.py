#Various Imports
import numpy as np
from collections import OrderedDict
import matplotlib.pyplot as plt
import h5py

data = h5py.File('/home/pablo/github/DeepIceLearning/my_code/l2_00000111.h5')
data.keys()

a=data['IC_charge']
a
b=a[:,:,:].flatten()
plt.hist(b)

b=data['IC_diff']
b
b=b[:,:,:].flatten()
plt.hist(b)

np.array(b)
np.histogram(b)

is.nan(b)

import h5py
import os
import tables
import sys
import numpy as np
import multiprocessing
import time

#python merge.py "/home/pablo/github/DeepIceLearning/notebooks/h5" "/home/pablo/github/DeepIceLearning/notebooks/h5_merged" 10

#inputfolder="/home/pablo/github/DeepIceLearning/notebooks/h5"
#outputfolder="/home/pablo/github/DeepIceLearning/notebooks/h5_merged"
#n=10  #number of output files (also simultaneous cpu usage)

inputfolder = sys.argv[1]
outputfolder = sys.argv[2]
n = int(sys.argv[3])

print("The computer has:", multiprocessing.cpu_count(),"CPU.","You are using:",n)

File_list=os.listdir(inputfolder)   #np.sort
Full_path_file_list = [os.path.join(inputfolder, path) for path in  File_list ]
Splited_Full_path_file_list=np.array_split(Full_path_file_list,n)
outputfile_list=[outputfolder+"/h5_merged{}.h5".format(i) for i in range(n) ]

def merge(file_and_output_file):
    #intput(Splited_Full_path_file_list[i],outputfile_list[i])
    #output outputfile_list[i]
    
    file_list,output_file=file_and_output_file
    input_shape = [10, 10, 60]
    FILTERS = tables.Filters(complib='zlib', complevel=9)

    hf1 = h5py.File(file_list[0], 'r')
    dtype=hf1["reco_vals"].dtype
    keys = list(hf1.keys())

    with tables.open_file(output_file, mode="w", title="Events for training the NN", filters=FILTERS) as h5file:

        input_features = []
        for okey in keys[:-1]:
            feature = h5file.create_earray(
                    h5file.root, okey, tables.Float64Atom(),
                    (0, input_shape[0], input_shape[1], input_shape[2], 1),
                    title=okey)
            feature.flush()
            input_features.append(feature)
        reco_vals = tables.Table(h5file.root, 'reco_vals', description=dtype)
        h5file.root._v_attrs.shape = input_shape
        hf1.close()
        it=0
        s=np.size(file_list)
        for file in file_list:
            print('Open {}'.format(file),it/s*100,"%")
            one_h5file = h5py.File(file, 'r')
            num_events = len(one_h5file["reco_vals"])
            for k in range(num_events):
                for i, okey in enumerate(keys[:-1]):
                    input_features[i].append(np.expand_dims(one_h5file[okey][k], axis=0))
                reco_vals.append(np.atleast_1d(one_h5file["reco_vals"][k]))
            for inp_feature in input_features:
                    inp_feature.flush()
            reco_vals.flush()
        one_h5file.close()

    print("Finished.")

file_and_output_file=[(Splited_Full_path_file_list[i],outputfile_list[i]) for i in range(n)]

ti = time.time()
p = multiprocessing.Pool(n)
p.map(merge,file_and_output_file)

p.close()
p.join()
tf=time.time()-ti
print("Total time elapsed:", tf,"s")
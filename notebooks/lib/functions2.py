import h5py
import time
import numpy as np
import math

def generator(batch_size, file_handlers, inds,
              inp_transformations, out_transformations,
              weighting_function=None, use_data=False, equal_len=False,
              mask_func=None):

    """ This function generates the training batches for the neural network.
    It load all input and output data and applies the transformations
    as defined in the network definition file.

    Arguments:
    batch size : the batch size per gpu
    file_handlers: list of files used for the training
                   i.e. ['/path/to/file/A', 'path/to/file/B']
    inds: the index range used for the files
          e.g. [(0,1000), (0,2000)]
    inp_shape_dict: A dictionary with the input shape for each branch
    inp_transformations: Dictionary with input variable name and function
    out_shape_dict: A dictionary with the output shape for each branch
    out_transformations: Dictionary with out variable name and function
    weighting_function: A function that returns the event weights on basis
                        of the information saved in reco_vals, e.g.
                        lambda mc: np.log10(mc['trunc_e'])
    mask_func: a function that returns a mask of values that get a 
                weight of zero, i.e. will not be considered in the loss
                e.g. lambda mc: mc['mu_e_on_entry'] < 1.e2
                        
    Returns:
    batch_input : a batch of input data
    batch_out: a batch of output data
    weights: a weight for each event

    """

#     print('Run with inds {}'.format(inds))

    in_branches = [(branch, inp_transformations[branch]['general'])
                   for branch in inp_transformations]
    out_branches = [(branch, out_transformations[branch]['general'])
                    for branch in out_transformations]
    inp_variables = [[(i, inp_transformations[branch[0]][i][1])
                      for i in inp_transformations[branch[0]] if i != 'general']
                     for branch in in_branches]
    out_variables = [[(i, out_transformations[branch[0]][i][1])
                      for i in out_transformations[branch[0]] if i != 'general']
                     for branch in out_branches]
    cur_file = 0
    ind_lo = inds[0][0]
    ind_hi = inds[0][0] + batch_size
    in_data = h5py.File(file_handlers[0], 'r')
    f_reco_vals = in_data['reco_vals']
    t0 = time.time()
    num_batches = 0
 
    while True:
        inp_data = []
        out_data = []
        weights = []
        arr_size = np.min([batch_size, ind_hi - ind_lo])
        reco_vals = f_reco_vals[ind_lo:ind_hi]

        #print('Generate Input Data')
        for k, b in enumerate(out_branches):
            for j, f in enumerate(out_variables[k]):
                if weighting_function != None:
                    tweights=weighting_function(reco_vals)
                else:
                    tweights=np.ones(arr_size)
                if mask_func != None:
                    mask = mask_func(reco_vals)
                    tweights[mask] = 0
            weights.append(tweights)
            
        for k, b in enumerate(in_branches):
            batch_input = np.zeros((arr_size,)+in_branches[k][1])
            for j, f in enumerate(inp_variables[k]):
                if f[0] in in_data.keys():
                    pre_data = np.array(np.squeeze(in_data[f[0]][ind_lo:ind_hi]), ndmin=4)
                    batch_input[:,:,:,:,j] = np.atleast_1d(f[1](pre_data))
                else:
                    pre_data = np.squeeze(reco_vals[f[0]])
                    batch_input[:,j]=f[1](pre_data)
            inp_data.append(batch_input)
            
        # Generate Output Data
        for k, b in enumerate(out_branches):
            if use_data:
                continue
            shape = (arr_size,)+out_branches[k][1]
            batch_output = np.zeros(shape)
            for j, f in enumerate(out_variables[k]):
                pre_data = np.squeeze(reco_vals[f[0]])
                if len(out_variables[k]) == 1:
                    batch_output[:]=np.reshape(f[1](pre_data), shape)
                else:
                    batch_output[:,j] = f[1](pre_data)
            out_data.append(batch_output)

        #Prepare Next Loop
        ind_lo += batch_size
        ind_hi += batch_size
        if (ind_lo >= inds[cur_file][1]) | (equal_len & (ind_hi > inds[cur_file][1])):
            cur_file += 1
            if cur_file == len(file_handlers):
                cur_file=0
            t1 = time.time()
#             print('\n Open File: {} \n'.format(file_handlers[cur_file]))
#             print('\n Average Time per Batch: {}s \n'.format((t1-t0)/num_batches))
            t0 = time.time()
            num_batches = 0
            in_data.close()
            in_data = h5py.File(file_handlers[cur_file], 'r')
            f_reco_vals = in_data['reco_vals']
            ind_lo = inds[cur_file][0]
            ind_hi = ind_lo + batch_size
        elif ind_hi > inds[cur_file][1]:
            ind_hi = inds[cur_file][1]
       
        # Yield Result
        num_batches += 1
        if use_data:
            yield inp_data
        else:
            yield (inp_data, out_data, weights)
            
            
def get_indices(dnn_files, batch_size):
    """ 
    This function calculates the length of the input files and the corresponding numbers
    of generator steps
    """
    train_inds = [(0, len(h5py.File(f, 'r')['reco_vals'])) for f in dnn_files['files_training']]
    valid_inds = [(0, len(h5py.File(f, 'r')['reco_vals'])) for f in dnn_files['files_validation']]
    test_inds = [(0, len(h5py.File(f, 'r')['reco_vals'])) for f in dnn_files['files_test']]
    train_steps = int(np.sum([math.ceil((1.*(k[1]-k[0])/batch_size))\
                                 for k in train_inds]))
    valid_steps = int(np.sum([math.ceil((1.*(k[1]-k[0])/batch_size))\
                                   for k in valid_inds]))
    test_steps = int(np.sum([math.ceil((1.*(k[1]-k[0])/batch_size))\
                                   for k in test_inds])) - 1
    return train_steps, valid_steps, test_steps, train_inds, valid_inds, test_inds

            
def IC_divide_1000(x, r_vals=None):
    return  x / 1000.

def IC_identity(x, r_vals=None):
    return x

def IC_log10(x, r_vals=None):
    return np.log10(1. * x)

def oneHotEncode_4_types(x, r_vals=None):
    """
    This function one hot encodes the input for the event types 
    cascade, tracks, doubel-bang, starting tracks
    """
    cascade = [1., 0., 0., 0.]
    track = [0., 1., 0., 0.]
    doublebang = [0., 0., 1., 0.]
    s_track = [0., 0., 0., 1.]
    # map x to possible classes
    mapping = {0: cascade, 1: track, 2: doublebang, 3: s_track}
    ret = np.zeros((len(x), 4))
    for i in mapping.keys():
        ret[x == i] = mapping[i]
    return ret


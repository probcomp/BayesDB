import argparse
#
import tabular_predDB.api_utils as au
import tabular_predDB.file_utils as fu

# issue is that M_c is using numpy.int64 instead of int

# parse some arguments
parser = argparse.ArgumentParser()
parser.add_argument('pkl_name', type=str)
parser.add_argument('--hostname', default='localhost', type=str)
parser.add_argument('--seed', default=0, type=int)
parser.add_argument('--start_id', default=0, type=int)
args = parser.parse_args()
pkl_name = args.pkl_name
hostname = args.hostname
seed = args.seed
id = args.start_id

# settings
URI = 'http://' + hostname + ':8007'
print 'URI: ', URI

save_dict = fu.unpickle(pkl_name)
method_name = 'analyze'
args_dict = dict()
args_dict['M_c'] = save_dict['M_c']
args_dict['T'] = save_dict['T']
args_dict['X_L'] = save_dict['X_L']
args_dict['X_D'] = save_dict['X_D']
args_dict['kernel_list'] = 'kernel_list'
args_dict['n_steps'] = 1
args_dict['c'] = 'c'
args_dict['r'] = 'r'
args_dict['max_iterations'] = 'max_iterations'
args_dict['max_time'] = 'max_time'
out, id = au.call(method_name, args_dict, URI, id)
X_L_prime, X_D_prime = out

import argparse
import time
import requests
import json
#
import numpy
#
import tabular_predDB.Engine as E
import tabular_predDB.cython.gen_data as gen_data


# parse some arguments
parser = argparse.ArgumentParser()
parser.add_argument('--hostname', default='localhost', type=str)
parser.add_argument('--seed', default=0, type=int)
parser.add_argument('--num_clusters', default=2, type=int)
parser.add_argument('--num_cols', default=8, type=int)
parser.add_argument('--num_rows', default=300, type=int)
parser.add_argument('--num_splits', default=2, type=int)
parser.add_argument('--max_mean', default=10, type=float)
parser.add_argument('--max_std', default=0.1, type=float)
parser.add_argument('--start_id', default=0, type=int)
args = parser.parse_args()
hostname = args.hostname
seed = args.seed
num_clusters = args.num_clusters
num_cols = args.num_cols
num_rows = args.num_rows
num_splits = args.num_splits
max_mean = args.max_mean
max_std = args.max_std
id = args.start_id

# settings
URI = 'http://' + hostname + ':8007'
print 'URI: ', URI

# helper functions
def create_message(method_name, params):
    global id
    id += 1
    message = {
        'jsonrpc': '2.0',
        'method': method_name,
        'params': params,
        'id': str(id),
        }
    return json.dumps(message)

def call(method_name, args_dict, print_message=False):
    message = create_message(method_name, args_dict)
    if print_message: print 'trying message:', message
    r = requests.put(URI, data=message)
    r.raise_for_status()
    out = json.loads(r.content)
    if isinstance(out, dict) and 'result' in out:
        return out['result']
    else:
        print "call(): ERROR"
        return out
def call_and_print(method_name, args_dict):
    out = call(method_name, args_dict, True)
    print out
    print
    return out


T, M_r, M_c = gen_data.gen_factorial_data_objects(
    seed, num_clusters,
    num_cols, num_rows, num_splits,
    max_mean=max_mean, max_std=max_std,
    )

# non-stub functions
non_stub = set(['initialize', 'initialize_and_analyze', 'analyze', 'impute',
                'simple_predictive_sample'])

method_name = 'initialize'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['M_r'] = M_r
args_dict['T'] = T
out = call(method_name, args_dict)
M_c, M_r, X_L_prime, X_D_prime = out

method_name = 'analyze'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['T'] = T
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['kernel_list'] = 'kernel_list'
args_dict['n_steps'] = 10
args_dict['c'] = 'c'
args_dict['r'] = 'r'
args_dict['max_iterations'] = 'max_iterations'
args_dict['max_time'] = 'max_time'
out = call(method_name, args_dict)
X_L_prime, X_D_prime = out
time.sleep(1)

method_name = 'simple_predictive_sample'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['Y'] = None
args_dict['q'] = [(0,0)]
values = []
for idx in range(10):
    out = call_and_print(method_name, args_dict)
    values.append(out[0])
print values
time.sleep(1)

method_name = 'impute'
args_dict = dict()
args_dict['M_c'] = 'M_c'
args_dict['X_L'] = 'X_L'
args_dict['X_D'] = 'X_D'
args_dict['Y'] = 'Y'
args_dict['q'] = range(3)
args_dict['n'] = 'n'
out = call(method_name, args_dict)
time.sleep(1)

# programmatically call all the other method calls
method_name_to_args = E.get_method_name_to_args()
for method_name, arg_str_list in method_name_to_args.iteritems():
    if method_name in non_stub:
        print 'skipping non-stub method:', method_name
        print
        continue
    args_dict = dict(zip(arg_str_list, arg_str_list))
    call_and_print(method_name, args_dict)
    time.sleep(1)

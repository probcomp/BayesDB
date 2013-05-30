#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import argparse
import time
#
import tabular_predDB.LocalEngine as LE
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.api_utils as au
import tabular_predDB.python_utils.general_utils as gu


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

T, M_r, M_c = du.gen_factorial_data_objects(
    seed, num_clusters,
    num_cols, num_rows, num_splits,
    max_mean=max_mean, max_std=max_std,
    )

# non-stub functions
non_stub = set(['initialize', 'initialize_and_analyze', 'analyze', 'impute',
                'impute_and_confidence', 'simple_predictive_sample'])

method_name = 'initialize'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['M_r'] = M_r
args_dict['T'] = T
out, id = au.call(method_name, args_dict, URI)
M_c, M_r, X_L_prime, X_D_prime = out

method_name = 'analyze'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['T'] = T
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['kernel_list'] = ()
args_dict['n_steps'] = 10
args_dict['c'] = ()
args_dict['r'] = ()
args_dict['max_iterations'] = 'max_iterations'
args_dict['max_time'] = 'max_time'
out, id = au.call(method_name, args_dict, URI)
X_L_prime, X_D_prime = out
time.sleep(1)

method_name = 'simple_predictive_sample'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['Y'] = None
args_dict['Q'] = [(0,0), (0,1)]
values = []
for idx in range(3):
    out, id = au.call_and_print(method_name, args_dict, URI)
    values.append(out[0])
print values
time.sleep(1)

method_name = 'impute'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['Y'] = None
args_dict['Q'] = [(0, 0)]
args_dict['n'] = 10
out, id = au.call(method_name, args_dict, URI)
time.sleep(1)

method_name = 'impute_and_confidence'
args_dict = dict()
args_dict['M_c'] = M_c
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['Y'] = None
args_dict['Q'] = [(0, 0)]
args_dict['n'] = 10
out, id = au.call(method_name, args_dict, URI)
time.sleep(1)

# programmatically call all the other method calls
method_name_to_args = gu.get_method_name_to_args(LE.LocalEngine)
for method_name, arg_str_list in method_name_to_args.iteritems():
    if method_name in non_stub:
        print 'skipping non-stub method:', method_name
        print
        continue
    args_dict = dict(zip(arg_str_list, arg_str_list))
    au.call_and_print(method_name, args_dict, URI)
    time.sleep(1)

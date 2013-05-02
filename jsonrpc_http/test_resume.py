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
#
import tabular_predDB.python_utils.api_utils as au
import tabular_predDB.python_utils.file_utils as fu


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

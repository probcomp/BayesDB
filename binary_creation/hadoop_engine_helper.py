#!/opt/anaconda/bin/python

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
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.jsonrpc_http.Engine as E


default_filename = 'hadoop_input.pkl.gz'
# parse input
parser = argparse.ArgumentParser()
parser.add_argument('inf_seed', default=0, type=int, nargs='?')
parser.add_argument('--filename', default=default_filename, type=str)
args = parser.parse_args()
#
filename = args.filename
SEED = args.inf_seed


def initialize_helper(hadoop_input, SEED):
    M_c = hadoop_input['M_c']
    M_r = hadoop_input['M_r']
    T = hadoop_input['T']
    initialization = hadoop_input['initialization']
    engine = E.Engine(SEED)
    M_c_prime, M_r_prime, X_L, X_D = engine.initialize(M_c, M_r, T)
    #
    ret_dict = dict(X_L=X_L, X_D=X_D)
    return ret_dict

def analyze_helper(hadoop_input, SEED):
    M_c = hadoop_input['M_c']
    T = hadoop_input['T']
    X_L = hadoop_input['X_L']
    X_D = hadoop_input['X_D']
    kernel_list = hadoop_input['kernel_list']
    n_steps = hadoop_input['n_steps']
    c = hadoop_input['c']
    r = hadoop_input['r']
    engine = E.Engine(SEED)
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=(),
                                          n_steps=n_steps, c=c, r=r,
                                          SEED=SEED,
                                          )
    #
    ret_dict = dict(X_L=X_L, X_D=X_D)
    return ret_dict

method_lookup = dict(
    initialize=initialize_helper,
    analyze=analyze_helper,
    )


# take all arguments from dictionary in file
hadoop_input = fu.unpickle(filename)
command = hadoop_input['command']
method = method_lookup[command]
ret_dict = method(hadoop_input)

# output for hadoop to write to file
print ret_dict

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
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.jsonrpc_http.Engine as E


default_filename = '../web_resources/data/dha.csv'
# parse input
parser = argparse.ArgumentParser()
parser.add_argument('inf_seed', default=0, type=int, nargs='?')
parser.add_argument('--filename', default=default_filename, type=str)
parser.add_argument('--gen_seed', default=0, type=int)
parser.add_argument('--num_transitions', default=10, type=int)
args = parser.parse_args()
#
inf_seed = args.inf_seed
filename = args.filename
gen_seed = args.gen_seed
num_transitions = args.num_transitions


# set everything up
T, M_r, M_c = du.read_model_data_from_csv(filename, gen_seed=gen_seed)
num_rows = len(T)
num_cols = len(T[0])

# do the computation
engine = E.Engine(inf_seed)
M_c_prime, M_r_prime, X_L, X_D = engine.initialize(M_c, M_r, T)
X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=(),
    n_steps=num_transitions)

# output for hadoop to write to file
print ','.join(map(str, [X_L_prime, X_D_prime]))

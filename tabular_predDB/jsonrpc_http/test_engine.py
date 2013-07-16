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
import numpy
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.cython_code.State as State
from tabular_predDB.jsonrpc_http.Engine import Engine


# parse input
parser = argparse.ArgumentParser()
parser.add_argument('--filename', default='testdata_kiva100files_mod.csv',
                    type=str)
parser.add_argument('--inf_seed', default=0, type=int)
parser.add_argument('--gen_seed', default=0, type=int)
parser.add_argument('--num_transitions', default=1000, type=int)
parser.add_argument('--N_GRID', default=31, type=int)
parser.add_argument('--max_rows', default=500, type=int)
args = parser.parse_args()
#
filename = args.filename
inf_seed = args.inf_seed
gen_seed = args.gen_seed
num_transitions = args.num_transitions
N_GRID = args.N_GRID
max_rows = args.max_rows


continuous_labels = set([
        'Lender Country GDP Score', 'Lender Join Date', 'Lender Loan count',
        'Lender Invitee Count', 'Borrower Country GDP Score',
        'Number of Borrowers', 'Funded Amount', 'Loan Amount'
        ])
multinomial_labels = set([
        'Lender Country Label', 'Lender Occupation Label', 'Lender URL Flag',
        'Borrower Country Label', 'Field Partner ID', 'Loan ID',
        'Loan Sector Label', 'Loan Status Label'
        ])

T, M_r, M_c, header = du.all_continuous_from_file(filename, max_rows, gen_seed)
is_multinomial = [label in multinomial_labels for label in header]
multinomial_column_indices = numpy.nonzero(is_multinomial)[0]
T, M_c = du.convert_columns_to_multinomial(T, M_c,
                                           multinomial_column_indices)


burn_in = 10
lag = 10
num_samples = 10
engine = Engine()

# initialize
kernel_list = None
c, r, max_iterations, max_time = None, None, None, None
X_L, X_D = engine.initialize(M_c, M_r, T)

# burn in 
X_L, X_D = engine.analyze(M_c, T, X_L, X_D, kernel_list, burn_in,
                          c, r, max_iterations, max_time)

# draw sample states
for sample_idx in range(num_samples):
    print "starting sample_idx #: %s" % sample_idx
    X_L, X_D = engine.analyze(M_c, T, X_L, X_D, kernel_list, lag,
                              c, r, max_iterations, max_time)
    p_State = State.p_State(M_c, T, X_L, X_D, N_GRID=N_GRID)
    plot_filename = 'sample_%s_X_D' % sample_idx
    pkl_filename = 'sample_%s_pickled_state.pkl.gz' % sample_idx
    p_State.save(filename=pkl_filename, M_c=M_c, T=T)
    p_State.plot(filename=plot_filename)

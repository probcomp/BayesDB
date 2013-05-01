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
import sys
from collections import Counter
#
import numpy
import pylab
pylab.ion()
pylab.show()
#
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.sample_utils as su


# parse some arguments
parser = argparse.ArgumentParser()
parser.add_argument('pkl_name', type=str)
parser.add_argument('--inf_seed', default=0, type=int)
args = parser.parse_args(['/usr/local/tabular_predDB/cython_code/iter_90_pickled_state.pkl.gz'])
pkl_name = args.pkl_name
inf_seed = args.inf_seed

random_state = numpy.random.RandomState(inf_seed)
# FIXME: getting weird error on conversion to int: too large from inside pyx
def get_next_seed(max_val=32767): # sys.maxint):
    return random_state.randint(max_val)

# resume from saved name
save_dict = fu.unpickle(pkl_name)
M_c = save_dict['M_c']
X_L = save_dict['X_L']
X_D = save_dict['X_D']
T = save_dict['T']
num_cols = len(X_L['column_partition']['assignments'])
row_idx = 205
col_idx = 13
Q = [(row_idx, col_idx)]
imputed, confidence = su.impute_and_confidence(
    M_c, X_L, X_D, Y=None, Q=Q, n=400, get_next_seed=get_next_seed)

T_array = numpy.array(T)
which_view_idx = X_L['column_partition']['assignments'][col_idx]
X_D_i = numpy.array(X_D[which_view_idx])
which_cluster_idx = X_D_i[row_idx]
which_rows_match_indices = numpy.nonzero(X_D_i==which_cluster_idx)[0]
cluster_vals = T_array[which_rows_match_indices, col_idx]
all_vals = T_array[:, col_idx]
cluster_counter = Counter(cluster_vals)
cluster_ratio = float(cluster_counter[imputed]) / sum(cluster_counter.values())
all_counter = Counter(all_vals)
all_ratio = float(all_counter[imputed]) / sum(all_counter.values())
print
print 'imputed: %s' % imputed
print 'all_ratio: %s' % all_ratio
print 'cluster_ratio: %s' % cluster_ratio
print 'confidence: %s' % confidence

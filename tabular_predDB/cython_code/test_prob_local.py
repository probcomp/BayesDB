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
import random
import argparse
import sys
from collections import Counter
import pdb
#
import numpy
import pylab

# import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.enumerate_utils as eu
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.python_utils.data_utils as du

import tabular_predDB.cython_code.State as State

random.seed(None)
inf_seed = random.randrange(32767)

# FIXME: getting weird error on conversion to int: too large from inside pyx
def get_next_seed(max_val=32767): # sys.maxint):
    return random_state.randint(max_val)

random_state = numpy.random.RandomState(inf_seed)

# generate a state with two, very distinct clusters
col = numpy.array([0,0])
row = numpy.array([[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]])

p_State, T, M_c = eu.GenerateStateFromPartitions(col,row,std_gen=1000.0, std_data=0.01)

X_L = p_State.get_X_L()
X_D = p_State.get_X_D()


# move stuff around a little bit
for i in range(100):
	p_State.transition(which_transitions=['column_partition_assignments','row_partition_assignments'])

# quick test just to make sure things output what they're supposed to 
x = 1.0;
query_row = len(row[0])
Q = [(query_row,0,x)]

Y = []
p = su.simple_predictive_probability(M_c, X_L, X_D, Y, Q, get_next_seed,n=100)

n = 1000;
samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed,n=n)

# X_diff = [x-sample[0] for sample in samples]
X_diff = [sample[0] for sample in samples]

pylab.hist(X_diff,50,normed=1, histtype='bar')
pylab.show()

Qs = [];
for i in range(n):
    Qtmp = (query_row,0,samples[i][0])
    Qs.append(Qtmp)

Ps,e = su.simple_predictive_probability(M_c, X_L, X_D, Y, Qs, get_next_seed,n=100)

Ps = numpy.exp(Ps)

# make a scatterplot
pylab.errorbar(X_diff,P_diff, yerr=e, fmt='ro', alpha=.8)
pylab.show()

print("Holding for input.")
pdb.set_trace()
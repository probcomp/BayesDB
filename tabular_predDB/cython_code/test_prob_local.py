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
import pdb
#
import numpy
import pylab

# import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.python_utils.data_utils as du

import tabular_predDB.cython_code.State as State

inf_seed = 0

# FIXME: getting weird error on conversion to int: too large from inside pyx
def get_next_seed(max_val=32767): # sys.maxint):
    return random_state.randint(max_val)

random_state = numpy.random.RandomState(inf_seed)

T, M_r, M_c = du.gen_factorial_data_objects(inf_seed, 10, 10, 10, 2);

M_c = du.gen_M_c_from_T(T)

p_State = State.p_State(M_c, T, N_GRID=100)
X_L = p_State.get_X_L()
X_D = p_State.get_X_D()


# quick test just to make sure things output what they're supposed to 
x = .1;
Q = [(0,2,x)]
Y = [(1,2,.3)]
p = su.simple_predictive_probability(M_c, X_L, X_D, Y, Q, get_next_seed)

# pdb.set_trace()

# the test is this:
# choose a single query, (r,c,x) with whatever contraints, Y
# get the simple predictive probability
# draw a bunch of samples from simple predictive probability
# get the predictive_probability of those samples 
# the mean predictive probability of the samples that are close to x should be close to 
# the predictive probabilty of x
n = 100;
samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed,n=n)

pdb.set_trace()
X_diff = [x-sample[0] for sample in samples]

Qs = [];
for i in range(n):
    Qtmp = (0,2,samples[i])
    Qs.append(Qtmp)

Ps = su.simple_predictive_probability(M_c, X_L, X_D, Y, Qs, get_next_seed)

P_diff = p[0]-Ps

# make a scatterplot
pylab.scatter(X_diff,P_diff,c='black',alpha=.5)
pylab.show()

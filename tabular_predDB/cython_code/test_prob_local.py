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

X = [sample[0] for sample in samples]

pylab.figure(facecolor='white')
pylab.hist(X,50,normed=1, histtype='bar',label='samples',edgecolor='none')
# pylab.show()

Qs = [];
for i in range(n):
    Qtmp = (query_row,0,samples[i][0])
    Qs.append(Qtmp)

Ps,e = su.simple_predictive_probability(M_c, X_L, X_D, Y, Qs, get_next_seed,n=100)

Ps = numpy.exp(Ps)

# make a scatterplot
pylab.errorbar(X,Ps, yerr=e, fmt='ro', alpha=.5, markersize=4,label='probability',markeredgecolor = 'none')
pylab.legend(loc='upper left')
pylab.xlabel('value') 
pylab.ylabel('frequency/probability')
pylab.title('TEST: probability and frequencies are not normalized')
pylab.show()

raw_input("Press Enter when finished...")
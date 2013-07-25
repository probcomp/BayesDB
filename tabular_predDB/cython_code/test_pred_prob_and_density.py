import random
import argparse
import sys
from collections import Counter
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
# THIS CODE ONLY TESTS CONTINUOUS DATA

# FIXME: getting weird error on conversion to int: too large from inside pyx
def get_next_seed(max_val=32767): # sys.maxint):
    return random_state.randint(max_val)

random_state = numpy.random.RandomState(inf_seed)

# generate a state with two, very distinct clusters
col = numpy.array([0,0])
row = numpy.array([[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]])

p_State, T, M_c, M_r, X_L, X_D = eu.GenerateStateFromPartitions(col,row,std_gen=10000.0, std_data=0.01)

X_L = p_State.get_X_L()
X_D = p_State.get_X_D()

# move stuff around a little bit
for i in range(100):
	p_State.transition(which_transitions=['column_partition_assignments','row_partition_assignments'])

# quick test just to make sure things output what they're supposed to 
x = 0.0;
query_row = len(row[0]) # tests unobserved
# query_row = 3;		# tests observed
Q = [(query_row,0,x)]


Y = [] # no contraints
# Y = [(1,0,.1),(3,0,.1),(22,0,105),(30,0,100)] # generic constraints

p = su.simple_predictive_probability(M_c, X_L, X_D, Y, Q)

n = 1000;
samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed,n=n)

X = [sample[0] for sample in samples]

pylab.figure(facecolor='white')
pdf, bins, patches = pylab.hist(X,50,normed=True, histtype='bar',label='samples',edgecolor='none')
pylab.show()

pdf_max = max(pdf)

Qs = [];
for i in range(n):
    Qtmp = (query_row,0,X[i])
    Qs.append(Qtmp)

Ps = su.simple_predictive_probability(M_c, X_L, X_D, Y, Qs)
Ps2 = su.simple_predictive_probability_density(M_c, X_L, X_D, Y, Qs)

Ps = (numpy.exp(Ps)/max(numpy.exp(Ps)))*pdf_max
Ps2 = (numpy.exp(Ps2)/max(numpy.exp(Ps2)))*pdf_max

# make a scatterplot
pylab.scatter(X,Ps, c='red',label="p from cdf")

pylab.legend(loc='upper left')
pylab.xlabel('value') 
pylab.ylabel('frequency/probability')
pylab.title('TEST: probability and frequencies are not normalized')
pylab.show()

raw_input("Press Enter when finished with probabilty...")

pylab.clf()
pdf, bins, patches = pylab.hist(X,50,normed=True, histtype='bar',label='samples',edgecolor='none')
pylab.scatter(X,Ps2, c='green',label="pdf")

pylab.legend(loc='upper left')
pylab.xlabel('value') 
pylab.ylabel('frequency/density')
pylab.title('TEST: probability and frequencies are not normalized')
pylab.show()

raw_input("Press Enter when finished with density...")
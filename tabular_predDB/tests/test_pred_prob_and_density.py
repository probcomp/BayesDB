import random
import argparse
import sys
from collections import Counter

import numpy
import pylab

import tabular_predDB.python_utils.enumerate_utils as eu
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.python_utils.data_utils as du

import tabular_predDB.cython_code.State as State

random.seed(None)
inf_seed = random.randrange(32767)
# THIS CODE ONLY TESTS CONTINUOUS DATA

def get_next_seed(max_val=32767):
    return random_state.randint(max_val)


random_state = numpy.random.RandomState(inf_seed)

# generate a state with two, very distinct clusters
col = numpy.array([0,0])
row = numpy.array([[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]])

query_row = len(row[0]) # tests unobserved
query_column = 1
# query_row = 3		# tests observed
Q = [(query_row, query_column)]

p_state, T, M_c, M_r, X_L, X_D = eu.GenerateStateFromPartitions(col,row,std_gen=10.0, std_data=.1)

T_array = numpy.array(T)
mu = numpy.mean(T_array[:,query_column])

X_L = eu.FixPriors(X_L,1.,mu,1.,1.,1.)
p_state = State.p_State(M_c, T, X_L=X_L, X_D=X_D, N_GRID=100)

X_L = p_state.get_X_L()
X_D = p_state.get_X_D()

Y = [] # no constraints
# Y = [(1,query_column,.1),(3,query_column,.1),(22,query_column,105),(30,query_column,100)] # generic constraints


n = 3000; # number of samples to take
samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed,n=n)

X_array = numpy.array(samples)

std_X = numpy.std(X_array)
mean_X = numpy.mean(X_array)

# filter out extreme values
X_filter_low = numpy.nonzero(X_array < mean_X-3.*std_X)[0]
X_filter_high = numpy.nonzero(X_array > mean_X+3.*std_X)[0]
X_filter = numpy.hstack((X_filter_low, X_filter_high))

X_array = numpy.delete(X_array, X_filter)

X = X_array.tolist()

pdf, bins, patches = pylab.hist(X,50,normed=1, histtype='bar',label='samples',edgecolor='none',alpha=.5)
pylab.show()

pdf_max = max(pdf)

Qs = [];
for x in X:
    Qtmp = (query_row, query_column, x)
    Qs.append(Qtmp)

Ps = su.simple_predictive_probability(M_c, X_L, X_D, Y, Qs, epsilon=.01)
Ps2 = su.simple_predictive_probability_density(M_c, X_L, X_D, Y, Qs)

Ps = (numpy.exp(Ps)/max(numpy.exp(Ps)))*pdf_max
# since Ps2 comes from the pdf, it should not need to be normalized
Ps2 = numpy.exp(Ps2)#/max(numpy.exp(Ps2)))*pdf_max


# make a scatterplot
pylab.scatter(X,Ps, c='red',label="p from cdf")

pylab.legend(loc='upper left')
pylab.xlabel('value') 
pylab.ylabel('frequency/probability')
pylab.title('TEST: probability and frequencies are not normalized')
pylab.show()

raw_input("Press Enter when finished with probabilty...")

pylab.clf()
pdf, bins, patches = pylab.hist(X,50,normed=1, histtype='bar',label='samples',edgecolor='none',alpha=.5)
pylab.scatter(X,Ps2, c='green',label="pdf")

pylab.legend(loc='upper left')
pylab.xlabel('value') 
pylab.ylabel('frequency/density')
pylab.title('TEST: probability and frequencies are not normalized')
pylab.show()

raw_input("Press Enter when finished with density...")

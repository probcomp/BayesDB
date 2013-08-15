import random
import argparse
import sys
from collections import Counter

import pdb

import numpy
import pylab

import tabular_predDB.python_utils.enumerate_utils as eu
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.python_utils.data_utils as du

import tabular_predDB.cython_code.State as State

random.seed(None) # seed with system time
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

p_state, T, M_c, M_r, X_L, X_D = eu.GenerateStateFromPartitions(col, row, std_gen=10.0, std_data=.1)

T_array = numpy.array(T)
mu = numpy.mean(T_array[:,query_column])

X_L = eu.FixPriors(X_L,1.,mu,1.,1.,1.)
p_state = State.p_State(M_c, T, X_L=X_L, X_D=X_D, N_GRID=100)

X_L = p_state.get_X_L()
X_D = p_state.get_X_D()

Y = [] # no constraints
# Y = [(1,query_column,.1),(3,query_column,.1),(22,query_column,105),(30,query_column,100)] # generic constraints

n = 3000; # number of samples to take

# pull n samples
samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed,n=n)

X_array = numpy.sort(numpy.array(samples))

std_X = numpy.std(X_array)
mean_X = numpy.mean(X_array)

# filter out extreme values
X_filter_low = numpy.nonzero(X_array < mean_X-2.*std_X)[0]
X_filter_high = numpy.nonzero(X_array > mean_X+2.*std_X)[0]
X_filter = numpy.hstack((X_filter_low, X_filter_high))
X_array = numpy.delete(X_array, X_filter)

# sort for area calculation later on
X_array = numpy.sort(X_array)

X = X_array.tolist()

# build the queries
Qs = [];
for x in X:
    Qtmp = (query_row, query_column, x)
    Qs.append(Qtmp)

# get probabilities 
probabilities = numpy.exp(su.simple_predictive_probability(M_c, X_L, X_D, Y, Qs, epsilon=.001))
# get pdf values
densities = numpy.exp(su.simple_predictive_probability_density(M_c, X_L, X_D, Y, Qs))

max_probability_value = max(probabilities)
max_density_value = max(densities)

# scale the probability values to the pdf for fit purposes. 
# the shape should be the same, but the probability values are based on
# epsilon. Density should not need to be scaled
probabilities = (probabilities/max_probability_value)*max_density_value

# test that the area under Ps2 and pdfs is about 1 
# calculated using the trapezoid rule
area_density = 0;
for i in range(len(X)-1):
	area_density += (X[i+1]-X[i])*(densities[i+1]+densities[i])/2.0

print "Area of PDF (should be close to, but not greater than, 1): " + str(area_density)

pylab.figure(facecolor='white')


# PLOT: probability vs samples distribution
# scale all histograms to be valid PDFs (area=1)
pylab.subplot(1,2,1)

pdf, bins, patches = pylab.hist(X,100,normed=1, histtype='stepfilled',label='samples',alpha=.5,color=[.5,.5,.5])
pylab.scatter(X,probabilities, c='red',label="p from cdf", edgecolor='none')

pylab.legend(loc='upper left',fontsize='x-small')
pylab.xlabel('value') 
pylab.ylabel('frequency/scaled probability')
pylab.title('simple_predictive_probability (scaled to max(pdf))')

# PLOT: desnity vs samples distribution
pylab.subplot(1,2,2)
pdf, bins, patches = pylab.hist(X,100,normed=1, histtype='stepfilled',label='samples', alpha=.5, color=[.5,.5,.5])
pylab.scatter(X,densities, c="red", label="pdf", edgecolor='none')

pylab.legend(loc='upper left',fontsize='x-small')
pylab.xlabel('value') 
pylab.ylabel('frequency/density')
pylab.title('TEST: PDF (not scaled)')

pylab.show()

raw_input("Press Enter when finished...")

########################################################
# do the test with multinomial data
# T, M_r, M_c= du.gen_factorial_data_objects(0,2,2,row.shape[1],1)
T, M_r, M_c= du.gen_factorial_data_objects(0,2,2,2,1)

T = numpy.array(T,dtype=int)
T = numpy.array(T,dtype=float)
if numpy.min(T) < 0:
	T = T - numpy.min(T)

T, M_c = du.convert_columns_to_multinomial(T, M_c, [0,1])

T = T.tolist()

pdb.set_trace()
state = State.p_State(M_c, T)

# pull n samples
samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed,n=n)
X_array = numpy.sort(numpy.array(samples))
X = X_array.tolist()

pdb.set_trace()####
# build the queries
Qs = [];
for x in X:
    Qtmp = (query_row, query_column, x)
    Qs.append(Qtmp)

# get probabilities 
probabilities = numpy.exp(su.simple_predictive_probability(M_c, X_L, X_D, Y, Qs, epsilon=.001))
# get pdf values
densities = numpy.exp(su.simple_predictive_probability_density(M_c, X_L, X_D, Y, Qs))

max_probability_value = max(probabilities)
max_density_value = max(densities)


pylab.clf()

# PLOT: probability vs samples distribution
# scale all histograms to be valid PDFs (area=1)
pylab.subplot(1,2,1)

pdf, bins, patches = pylab.hist(X,100,normed=1, histtype='stepfilled',label='samples',alpha=.5,color=[.5,.5,.5])
pylab.scatter(X,probabilities, c='red',label="p from cdf", edgecolor='none')

pylab.legend(loc='upper left',fontsize='x-small')
pylab.xlabel('value') 
pylab.ylabel('frequency/scaled probability')
pylab.title('simple_predictive_probability (scaled to max(pdf))')

# PLOT: desnity vs samples distribution
pylab.subplot(1,2,2)
pdf, bins, patches = pylab.hist(X,100,normed=1, histtype='stepfilled',label='samples', alpha=.5, color=[.5,.5,.5])
pylab.scatter(X,densities, c="red", label="pdf", edgecolor='none')

pylab.legend(loc='upper left',fontsize='x-small')
pylab.xlabel('value') 
pylab.ylabel('frequency/density')
pylab.title('TEST: PDF (not scaled)')

pylab.show()





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


def get_next_seed(max_val=32767):
    return random_state.randint(max_val)


def run_test(n=1000, d_type='continuous', observed=False):
	if d_type == 'continuous':
		run_test_continuous(n, observed)
	elif d_type == 'multinomial':
		run_test_multinomial(n, observed)

def run_test_continuous(n, observed):
	n_rows = 40
	n_cols = 40

	if observed:
		query_row = 10
	else:
		query_row = n_rows

	query_column = 1

	Q = [(query_row, query_column)]

	# do the test with multinomial data
	T, M_r, M_c= du.gen_factorial_data_objects(get_next_seed(),2,2,n_rows,1)

	state = State.p_State(M_c, T)

	T_array = numpy.array(T)

	X_L = state.get_X_L()
	X_D = state.get_X_D()

	Y = [] # no constraints
	
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


def run_test_multinomial(n, observed):
	n_rows = 40
	n_cols = 40

	if observed:
		query_row = 10
	else:
		query_row = n_rows

	query_column = 1

	Q = [(query_row, query_column)]

	# do the test with multinomial data
	T, M_r, M_c= du.gen_factorial_data_objects(get_next_seed(),2,2,n_rows,1)

	T = numpy.array(T,dtype=int)
	T = numpy.array(T,dtype=float)
	if numpy.min(T) < 0:
		T = T - numpy.min(T)

	T, M_c = du.convert_columns_to_multinomial(T, M_c, [0,1])
	T = T.tolist()

	state = State.p_State(M_c, T)

	X_L = state.get_X_L()
	X_D = state.get_X_D()

	Y = []

	# pull n samples
	samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed,n=n)
	X_array = numpy.sort(numpy.array(samples))
	X = X_array.tolist()

	# build the queries
	# pdb.set_trace()
	Qs = [];
	for x in X:
	    Qtmp = (query_row, query_column, x[0])
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
	mbins = numpy.unique(X_array)

	mbins = numpy.append(mbins,max(mbins)+1)

	pdf, bins = numpy.histogram(X_array,mbins)
	p_unique = numpy.unique(probabilities)

	pdf = pdf/float(numpy.sum(pdf))
	pylab.bar(mbins[0:-1],pdf,label="samples",alpha=.5)
	# pdb.set_trace()
	pylab.scatter(X,probabilities, c='red',label="p from cdf", edgecolor='none')

	pylab.legend(loc='upper left',fontsize='x-small')
	pylab.xlabel('value') 
	pylab.ylabel('frequency/scaled probability')
	pylab.title('simple_predictive_probability (scaled to max(pdf))')

	# PLOT: desnity vs samples distribution
	pylab.subplot(1,2,2)
	pylab.bar(mbins[0:-1],pdf,label="samples",alpha=.5)
	pylab.scatter(X,densities, c="red", label="pdf", edgecolor='none')

	pylab.legend(loc='upper left',fontsize='x-small')
	pylab.xlabel('value') 
	pylab.ylabel('frequency/density')
	pylab.title('TEST: PDF (not scaled)')

	pylab.show()

	raw_input("Press Enter when finished...")

random.seed(None) # seed with system time
inf_seed = random.randrange(32767)
random_state = numpy.random.RandomState(inf_seed)


run_test(n=1000, d_type='continuous', observed=False)
run_test(n=1000, d_type='continuous', observed=True)
run_test(n=1000, d_type='multinomial', observed=False)
run_test(n=1000, d_type='multinomial', observed=True)

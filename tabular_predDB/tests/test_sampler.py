import numpy as np
import random
import pdb

# FIXME: this is a hack and should be fixed to inclue test utils as a module:
# import tabular_predDB.python_utils.test_utils as tu
import sys
sys.path.insert(0, '../python_utils/')

import test_utils as tu
import tabular_predDB.cython_code.State as State
import pylab
from scipy.stats import pearsonr as pearsonr

# Do we want to plot the results?
do_plot = True

if do_plot:
	pylab.ion()
	pylab.figure(facecolor="white",figsize=(10,10))


random.seed(None)

# priors
alpha = 1.0;
mu = 0.0;
r = 1.0;
nu = 1.0;
s = 1.0;

# matrix size
n_rows = 3
n_cols = 3

# sampler details
iters = 1000	# number of samples
burns = 20	# burn in before collection

# the number of states to correlate for the test (the n most probable)
n_highest = 20

# enumerate all state partitions
state_partitions = tu.CrossCatPartitions(n_rows, n_cols)
NS = state_partitions.N;

# the number of states to run the test on (randomly seelected)
n_states = 10;

print "Testing the sampler against enumerated answer for data generated from \n%i random states." % n_states

# for state in random.sample(state_partitions.states, n_states):
for state in state_partitions.states:

	progress = "[State %i] Collecting samples..." % (state['idx'])
	sys.stdout.write(progress)

	# Generate data from this state partition
	T, M_r, M_c = tu.GenDataFromPartitions(state['col_parts'], state['row_parts'], 0, 10, .5)
	# calculate the probability of the data under each state
	P = np.exp(tu.CCML(state_partitions, T, mu, r, nu, s, alpha, alpha))
	# print "done."
	
	# initialize state samples counter
	state_count = np.zeros(NS)

	# print "Sampling..."
	# start collecting samples
	# initalize the sampler
	p_State = State.p_State(M_c, T, N_GRID=100)
	X_L = tu.FixPriors(p_State.get_X_L(), alpha, mu, s, r, nu)
	X_D = p_State.get_X_D()
	p_State = State.p_State(M_c, T, N_GRID=100, X_L=X_L, X_D=X_D)


	for b in range(200):
		p_State.transition(which_transitions=['column_partition_assignments','row_partition_assignments'])

	mlen = 0;
	for j in range(iters):
		for b in range(burns):
			p_State.transition(which_transitions=['column_partition_assignments','row_partition_assignments'])

		progress1 = "%i of %i" % (j, iters)
		progress = "%s%s" % ('\b'*mlen, progress1)
		mlen = len(progress1)
		sys.stdout.write(progress)
		sys.stdout.flush()

		# collect a sample
		# get the colum partitions
		scp = p_State.get_column_partition()['assignments']
		# get the row partitions
		srp = p_State.get_X_D()
		# match the state
		state_idx = state_partitions.findState(scp, srp)
		state_count[state_idx] += 1.0

	print "%sdone.%s" % ('\b'*mlen, ' '*mlen)
	# normalize
	state_count = state_count/sum(state_count)
	
	# assert(sum(state_count) == 1.0)
	# assert(sum(P) == 1.0)

	# get the n_highest higest probability states
	sorted_indices = np.argsort(P)
	true_highest_probs = P[sorted_indices[-n_highest:]]
	inferred_highest_probs = state_count[sorted_indices[-n_highest:]]

	assert(len(true_highest_probs) == n_highest)
	assert(len(inferred_highest_probs) == n_highest)

	# correlation (two-tailed p value)
	PR = pearsonr(true_highest_probs, inferred_highest_probs) 

	# print "Higest probability states"
	# print true_highest_probs
	# print "Inferred"
	# print inferred_highest_probs
	print "\tCorrelation, (R,p)" + str(PR)

	if do_plot:
		pylab.clf()

		X = range(NS)
		pylab.subplot(2,1,1,title="All states")
		pylab.plot(X,P, color="blue", linewidth=2.5, linestyle="-", label="enumeration",alpha=.5)
		pylab.plot(X,state_count, color="red", linewidth=2.5, linestyle="-", label="sampler",alpha=.5)
		pylab.xlim(0,NS)
		pylab.legend(loc='upper right')

		X = range(n_highest)
		pylab.subplot(2,1,2,title=("%i highest probability states" % n_highest))
		pylab.plot(X,true_highest_probs[::-1], color="blue", linewidth=2.5, linestyle="-",label="enumeration",alpha=.5)
		pylab.plot(X,inferred_highest_probs[::-1], color="red", linewidth=2.5, linestyle="-",label="sampler",alpha=.5)
		pylab.xlim(0,n_highest)
		pylab.legend(loc='upper right')
		pylab.draw()
		
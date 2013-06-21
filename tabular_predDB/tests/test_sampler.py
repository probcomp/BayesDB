import numpy as np
import random
import pdb

# FIXME: this is a hack and should be fixed to inclue test utils as a module:
# import tabular_predDB.python_utils.test_utils as tu
import sys
sys.path.insert(0, '../python_utils/')

import test_utils as tu
import tabular_predDB.cython_code.State as State

from scipy.stats import pearsonr as pearsonr

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
iters = 400	# number of independent samples (chains)
burns = 200	# burn in before collection

# the number of states to correlate for the test (the n most probable)
n_highest = 20

# enumerate all state partitions
state_partitions = tu.CrossCatPartitions(n_rows, n_cols)

# the number of states to run the test on (randomly seelected)
n_states = 1;

for state in random.sample(state_partitions.states, n_states):
	
	print "[State " + str(state['idx']) + "] Collecting samples..."
	# print "Calculating true probablity via enumeration..."
	# Generate data from this state partition
	T, M_r, M_c = tu.GenDataFromPartitions(state['col_parts'], state['row_parts'], 0, 10, .5)
	# calculate the probability of the data under each state
	P = tu.CCML(state_partitions, T, mu, r, nu, s, alpha, alpha)
	# print "done."
	# initalize the sampler
	p_State = State.p_State(M_c, T, N_GRID=100)
	X_L = tu.FixPriors(p_State.get_X_L(), alpha, mu, s, r, nu)
	X_D = p_State.get_X_D()

	# initialize state samples counter
	state_count = np.zeros(state_partitions.N)

	# print "Sampling..."
	# start collecting samples
	for j in range(iters):
		for b in range(burns):
			p_State.transition(which_transitions=['column_partition_assignments','row_partition_assignments'])

		sys.stdout.write(".")
		sys.stdout.flush()
		if (j%50) == 0 and j > 0:
			print " %i of %i" % (j, iters)

		# collect a sample
		# get the colum partitions
		scp = p_State.get_column_partition()['assignments']
		# get the row partitions
		srp = p_State.get_X_D()
		# match the state
		state_idx = state_partitions.findState(scp, srp)
		state_count[state_idx] += 1.0

	print "done."
	# normalize
	state_count = state_count/sum(state_count);

	# get the n_highest higest probability states
	sorted_indices = np.argsort(P)
	true_highest_probs = exp(P[sorted_indices[0:n_highest]]) # answer in log
	inferred_highest_probs = state_count[sorted_indices[0:n_highest]]

	assert(len(true_highest_probs) == n_highest)
	assert(len(inferred_highest_probs) == n_highest)

	# correlation (two-tailed p value)
	PR = pearsonr(true_highest_probs, inferred_highest_probs) 

	print "Higest probability states"
	print true_highest_probs
	print "Inferred"
	print inferred_highest_probs
	print "Correlation, (R,p)" + str(PR)

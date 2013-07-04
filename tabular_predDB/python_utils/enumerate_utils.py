# A set of utilities that help with generating random states and calculating
# their probabilities.
# Functions list: 
#  1.GenerateRandomState(): Generates a random state and fills with gaussian data
#  2.GenerateRandomPartition(): Generates a random state (partitions only)
#  3.CRP(): Generates an assignment vector according to the CRP
#  4.pflip(): flips an n-dimensional hypercoin
#  5.GenDataFromPartitions(): generates data adhearing to a partitioning scheme
#  6.Bell(): Returns the Bell number
#  7.Stirling2nd(): Returns the Stirling number of the 2nd kind, s(n,k)
#  8.lcrp(): returns the log probability of a partition under the CRP
#  9.NGML(): calculates the Normal-Gamma marginal likelihood
# 10.CCML(): Calculates the marginal likelihood of a continuous data array under CrossCat
# 11.FixPriors(): Changes the priors in X_L
# 12.vectorToCHMat(): converts Assignment vector to cohabitation matrix (for state matching)
# 13.(class) CrossCatPartitions: Partition object. Enumerates all states.
# 14.(class) Partition: Used to enumerate partitions for CrossCatPartitions

from time import time

import math

import random as rand
import numpy as np
import scipy as sp
import itertools
import pdb

import tabular_predDB.cython_code.State as State
import tabular_predDB.python_utils.data_utils as du


# generates from a state with the columns to views partition col_parts, and 
# the rows in views to cats partition row_parts (X_D). Accepts partitions
# as numpy array or lists. Returns a state; the data table, T; and M_c
# Arguments:
#	col_parts : vector of length n_cols assigning columns to views
#	row_parts : a list of vectors (or numpy array) with n_views rows where
#				each row, i, is a vector assigning the rows of the columns 
#				in view i to categories
#	mean_gen  : the mean of the means of data clusters
#	std_gen   : the standard deviation of cluster means
#	std_data  : the standard deviation of the individual clusters
def GenerateStateFromPartitions(col_parts, row_parts, mean_gen=0.0, std_gen=1.0, std_data=0.1):
	
	T, M_r, M_c = GenDataFromPartitions(col_parts, row_parts, mean_gen=mean_gen, std_gen=std_gen, std_data=std_data)
	state = State.p_State(M_c, T, N_GRID=100)

	X_L = state.get_X_L()
	X_D = state.get_X_D()

	if type(col_parts) is not list:
		X_L['column_partition']['assignments'] = col_parts.tolist()

	if type(row_parts) is not list:
		X_D = row_parts.tolist()

	# create a new state with the updated X_D and X_L
	state = State.p_State(M_c, T, X_L=X_L, X_D=X_D, N_GRID=100)

	return state, T, M_c, M_r, X_L, X_D

# generates a random state with n_rows rows and n_cols columns, fills it with 
# normal data and the specified alphas, and prepares it for running. Returns 
# a State.p_state object and the table of data and M_c
# Arguments:
#	n_rows    : the number of rows
#	n_cols    : the number of columns
#	mean_gen  : the mean of the means of data clusters
#	std_gen   : the standard deviation of cluster means
#	std_data  : the standard deviation of the individual clusters
#	alpha_col : the CRP parameter for columns to views
# 	alpha_rows: the CRP parameter for rows into categories
def GenerateRandomState(n_rows, n_cols, mean_gen=0.0, std_gen=1.0, std_data=0.1, alpha_col=1.0, alpha_rows=1.0):

	# check the inputs 
	assert(type(n_rows) is int)
	assert(type(n_cols) is int)
	assert(type(mean_gen) is float)
	assert(type(std_gen) is float)
	assert(type(std_data) is float)
	assert(type(alpha_col) is float)
	assert(type(alpha_rows) is float)
	assert(n_rows > 0)
	assert(n_cols > 0)
	assert(std_gen > 0.0)
	assert(std_data > 0.0)
	assert(alpha_col > 0.0)
	assert(alpha_rows > 0.0)

	# generate the partitioning
	part = GenerateRandomPartition(n_rows, n_cols, alpha_col, alpha_rows)

	# fill it with data
	state, T, M_c, M_r, X_L, X_D = GenDataFromPartitions(part['col_parts'], part['row_parts'], mean_gen, std_gen, std_data)

	# this part is kind of hacky:
	# generate a state from the prior 
	state = State.p_State(M_c, T, N_GRID=100)
	# get the X_L and X_D and implant part['col_parts'], part['row_parts'], then 
	# create a new state with the new X_L and X_D defined
	X_L = state.get_X_L()
	X_D = state.get_X_D()

	# this should be all we need to change for 
	# State.transform_latent_state_to_constructor_args(X_L, X_D) to be able
	# to construct the arguments to intialize a state
	X_L['column_partition']['assignments'] = part['col_parts'].tolist()
	X_D = part['row_parts'].tolist()

	# hack in the alpha values supplied (or not) by the user
	X_L['column_partition']['hypers']['alpha'] = alpha_col
	for i in range(len(X_L['view_state'])):
		X_L['view_state'][i]['row_partition_model']['hypers']['alpha'] = alpha_col
	for i in range(n_cols):
		X_L['column_hypers'][i]['alpha'] = alpha_rows

	# create a new state with the updated X_D and X_L
	state = State.p_State(M_c, T, X_L=X_L, X_D=X_D, N_GRID=100)

	# pdb.set_trace()

	return state, T, M_c

# generates a random partitioning of n_rows rows and n_cols columns based on the
# CRP. The resulting partition is a dict with two entries: ['col_parts'] and
# ['row_parts']. See CrossCatPartitions for details on these.
def GenerateRandomPartition(n_rows, n_cols, alpha_col=1.0, alpha_rows=1.0):
	assert(type(n_rows) is int)
	assert(type(n_cols) is int)
	assert(type(alpha_col) is float)
	assert(type(alpha_rows) is float)
	assert(n_rows > 0)
	assert(n_cols > 0)
	assert(alpha_col > 0.0)
	assert(alpha_rows > 0.0)

	column_partition = CRP(n_cols, alpha_col)
	n_views = max(column_partition)+1;	

	row_partition = np.zeros(shape=(n_views,n_rows),dtype=int)

	for i in range(n_views):
		row_partition_tmp = CRP(n_rows, alpha_rows)
		row_partition[i] = row_partition_tmp

	partition = dict();
	partition['col_parts'] = column_partition;
	partition['row_parts'] = row_partition;

	assert(len(column_partition)==n_cols)
	assert(row_partition.shape[0]==n_views)
	assert(row_partition.shape[1]==n_rows)

	return partition

# Generates an N-length partitioning through the Chinese Restauraunt Process 
# with discount parameter alpha
def CRP(N,alpha):
	assert(type(N) is int)
	assert(type(alpha) is float)
	assert(N > 0)
	assert(alpha > 0.0)

	partition = np.zeros(N,dtype=int);

	for i in range(1,N):
		K = max(partition[0:i])+1;
		ps = np.zeros(K+1)
		for k in range(K):
			# get the number of people sitting at table k
			Nk = np.count_nonzero(partition[0:i]==k);
			ps[k] = Nk/(i+alpha)
		
		ps[K] = alpha/(i+alpha)

		assignment = pflip(ps)

		partition[i] = assignment

	assert(len(partition)==N)

	return partition

# flips an n-sided hypercoin
def pflip(P):
	# seed the RNG with system time
	rand.seed(None)
	if type(P) is float:
		if P > 1 or P < 0:
			print "Error: pflip: P is a single value not in [0,1]. P=" + str(P)
		else:
			return 1 if rand.random() > .5 else 0
	elif type(P) is np.ndarray:
		# normalize the list
		P = P/sum(P)
		P = np.cumsum(P)
		rdex = rand.random()
		# return the first entry greater than rdex	
		return np.nonzero(P>rdex)[0][0]
	else:
		print "Error: pflip: P is an invalid type."

# Generates T, M_c, and M_r fitting the state defined by col_part and row_part.
# Generates only continuous data.
def GenDataFromPartitions(col_part,row_parts,mean_gen,std_gen,std_data):
	n_cols = len(col_part)
	n_rows = row_parts.shape[1]

	seed = int(time()*100)
	np.random.seed(seed)

	T = np.zeros((n_rows,n_cols))

	for col in range(n_cols):
		view = col_part[col]-1
		row_part = row_parts[view,:]
		cats = max(row_part)
		for cat in range(cats):
			row_dex = np.nonzero(row_part==cat+1)[0]
			n_rows_cat = len(row_dex)
			mean = np.random.normal(mean_gen,std_gen)
			X = np.random.normal(mean,std_data,(n_rows_cat,1))
			i = 0
			for row in row_dex:
				T[row,col] = X[i]
				i += 1

	T.tolist()
	M_r = du.gen_M_r_from_T(T)
	M_c = du.gen_M_c_from_T(T)

	return T, M_r, M_c

# CrossCatPartitions 
# enumerates all states with n_rows rows and n_cols columns. This should not be 
# used for anything bigger than 4-by-4. If you want to generate large states, 
# generate them randomly using GenerateRandomPartition
#
# Attributes:
#	.N 		- The number of states
# 	.states - A list of state dicts. Each state has:
#		['idx'] 	 : an integer index of the state
#		['col_parts']: a n_cols length vector assigning columns to views.
#			Ex. state['col_parts'] = [0 0 1] implies that columns 0 and 1 are 
#				assigned to view 0 and column 2 is assigned to view 1.
#		['row_parts']: a n_views-length list of n_rows-length vectors. 
#			Each entry, i, assigns the row to a category. 
#			Ex. state['row_parts'] = [ [0 0 1], [0 0 0] ] implies that there are
#				two views. In the first view, the rows 0 and 1 are assigned to 
#				category 0 and row 2 is assigned to category 1. In the second 
#				view, all rows are assigned to category 0.
class CrossCatPartitions(object):

	def __init__(self,n_rows, n_cols):
		# Holds the total number of partitionings
		self.N = 0;
		Bn = Bell(n_rows);

		# Generate the column partitons (views)
		self.col_partition = Partition.EnumeratePartitions(n_cols)

		# Generate the possible row partition
		self.row_partition = Partition.EnumeratePartitions(n_rows)

		# each entry of the list row_perms holds the permutation of 
		# row_partition for for each view. So if row_perm[1][2] = (0,2) it means
		# that there are two views in the second view  partitioning and that in 
		# the third permutation that the rows in view 0 are partitions according
		# to self.row_partition[0] and that the rows in the second view are 
		# partitioned according to self.row_partition[2]
		self.row_perms = [];

		# for each partition, generate the partitioning of the rows of each view 
		# into categories (cells)
		for i in range(0,self.col_partition.shape[1]):
			# get the number of partitions
			K = i+1
			r = range(1,int(Bn)+1)

			# generate the permutations with replacement
			perms = [];
			for t in itertools.product(r, repeat = K):
				perms.append(t)

			self.row_perms.append(perms)


		for i in range(0,self.col_partition.shape[0]):
			K = int(self.col_partition[i].max())
			self.N += int(pow(Bn,K))

		self.states = []
		state_idx = 0
		for col_part in range(self.col_partition.shape[0]):
			K = int(max(self.col_partition[col_part]))
			n_views = int(max(self.col_partition[col_part]))
			# self.states[state_idx]= dict()
			for rprt in range(len(self.row_perms[n_views-1])):
				temp_state = dict()
				temp_state['idx'] = state_idx
				temp_state['col_parts'] = self.col_partition[col_part]
				this_row_partition = self.row_perms[n_views-1][rprt][0]-1
				temp_row_parts = np.array([self.row_partition[this_row_partition]])
				for view in range(1,n_views):
					this_row_partition = self.row_perms[n_views-1][rprt][view]-1
					temp_row_parts = np.vstack((temp_row_parts,self.row_partition[this_row_partition]))
				temp_state['row_parts'] = temp_row_parts
				self.states.append(temp_state)
				
				state_idx += 1


	def getState(self, state_num):
		if state_num < 0 or state_num > self.N-1:
			return None
		else:
			return self.states[state_num]

	def findState(self, col_part, row_parts):
		if min(col_part) == 0:
			n_views = max(col_part) + 1
		else:
			n_views = max(col_part)

		col_part_cm = vectorToCHMat(col_part);

		for state in range(len(self.states)):
			this_col_part = self.states[state]['col_parts']
			if max(this_col_part) != n_views:
				continue

			if not np.all(col_part_cm == vectorToCHMat(this_col_part)):
				continue

			for view in range(n_views):

				this_row_part = self.states[state]['row_parts'][view]

				if np.all(vectorToCHMat(row_parts[view])==vectorToCHMat(this_row_part)):
					if view == n_views-1:
						return self.states[state]['idx']
				else:
					break
			
		print "Error: no state match found"
		return none

	def test(self):
		print "Testing CrossCatPartitions"
		error = False
		# make sure findState returns the appropriate state number
		for state in self.states:
			cols = state['col_parts']
			rows = state['row_parts']
			found_index = self.findState(cols,rows)
			if state['idx'] != found_index:
				error = True
				print " "
				print "findState returned incorrect state (%i instead of %i). " % found_index, state['idx']
				print "Found state: "
				print "Cols"
				print(self.states[found_index]['col_parts'])
				print "Rows"
				print(self.states[found_index]['row_parts'])
				print "Actual state: "
				print "Cols"
				print(cols)
				print "Rows"
				print(rows)
				print " "
			# make sure state mathces after set to zero index
			cols = cols - 1
			rows = rows - 1
			found_index = self.findState(cols,rows)
			if state['idx'] != found_index:
				error = True
				print " "
				print "findState returned incorrect for relabled state (%i instead of %i). " % found_index, state['idx']
				print "Found state: "
				print "Cols"
				print(self.states[found_index]['col_parts'])
				print "Rows"
				print(self.states[found_index]['row_parts'])
				print "Actual state: "
				print "Cols"
				print(cols)
				print "Rows"
				print(rows)
				print " "

		if error:
			print("Test failed.")
		else:
			print("All tests passed.")

# partition class
# The thing we want is the EnumeratePartitions static  method. The Next function 
# doesn't actually stop itself so know that if you're going to try to use this 
# code elsewhere
class Partition(object):

	def __init__(self, N):
		self.N = N
		self.proceed = True
		self.s = np.ones(N, dtype=int)
		self.m = np.ones(N, dtype=int)
		
	# Enumerates the set of all partitionings of N points
	@staticmethod
	def EnumeratePartitions(N):
		p = Partition(N)

		expectedPartitions = Bell(N)
		currentPartition = 2

		C = np.copy(p.s)
	    
		while p.proceed:
			p.Next()
			if p.proceed:
				C = np.vstack([C,p.s]);
				currentPartition += 1
			else:
				break

			if currentPartition > expectedPartitions:
				break

		return C

	# generates the next partition
	def Next(self):
		n = self.N
		i = 0;
		self.s[i] = self.s[i] + 1;
		while (i < n) and (self.s[i] > self.m[i+1] + 1):
			self.s[i] = 1;
			i += 1;
			self.s[i] += 1
	    
		if self.s[i] > self.m[i]:
			self.m[i] = self.s[i]
        
		for j in range(i-1,-1,-1):
			self.m[j] = self.m[i]
        
		self.proceed = True;
	    

# returns B_N, the Nth Bell number. Uses the definition as a sum of Striling 
# numbers of the second kind. http://en.wikipedia.org/wiki/Bell_number
def Bell(N):
	B_N = 0.0;
	# range(n) produces an array 0,1,...,n-1
	for k in range(N+1):
		snk = Stirling2nd(N,k)
		B_N += snk
	
	return B_N

# Returns the Striling number of the second kind. Math taken from Wikipedia:
# http://en.wikipedia.org/wiki/Stirling_numbers_of_the_second_kind
def Stirling2nd(n,k):
	snk = 0.0;
	const = (1.0/math.factorial(k));
	for j in range(k+1):
		p1 = math.pow(-1,k-j)
		p2 = sp.special.binom(k,j)
		p3 = math.pow(j,n)
		snk += p1*p2*p3
	
	return const*snk

# Log CRP
# log probability of the partitioning, prt, under the CRP with concentration 
# parameter, alpha.
def lcrp(prt,alpha):
	# generate a histogram of prt
	k = max(prt)
	ns = np.zeros(k)
	n = len(prt)
	for i in range(n):
		ns[prt[i]-1] += 1.0

	lp = sum(sp.special.gammaln(ns))+k*math.log(alpha)+sp.special.gammaln(alpha)-sp.special.gammaln(n+alpha)

	if np.any(np.isnan(lp)) or np.any(np.isinf(lp)):
		print("prt: ")
		print(prt)
		print("ns: ")
		print(ns)
		print("n: " + str(n))
		print("k: " + str(k))
		print(range(k))
		print(" ")

	return lp

# Normal-Gamma marginal likelihood 
# Taken from Yee Whye Teh's "The Normal Exponential Family with 
# Normal-Inverse-Gamma Prior"
# http://www.stats.ox.ac.uk/~teh/research/notes/GaussianInverseGamma.pdf
def NGML(X,mu,r,nu,s):

	X = np.array(X.flatten(1))

	# constant
	LOGPI = np.log(math.pi)

	n = float(len(X)) 	# number of data points
	xbar = np.mean(X)	

	# update parameters
	rp  = r + n;
	nup = nu + n;
	mup = (r*mu+sum(X))/(r+n);
	spr = s + sum(X**2)+r*mu**2-rp*mup**2

	# the log answer
	lp1 = (-n/2)*LOGPI - (1/2)*np.log(rp)-(nup/2)*np.log(spr)+sp.special.gammaln(nup/2);
	lp2 = -(1/2)*np.log(r)-(nu/2)*np.log(s)+sp.special.gammaln(nu/2);
	lp = lp1-lp2;

	if np.isnan(lp):
		# print "X"
		# print(X)
		# print "X-xbar"
		# print(X-xbar)
		# print"sum((X-xbar)**2): %f" % sum((X-xbar)**2)
		print "xbar: %f" % xbar
		print "nu_n: %f" % nu_n
		print "mu_n: %f" % mu_n
		print "k_n: %f" % k_n
		print "s_n: %f" % s_n
		print "lp1: %f" % lp1
		print "lp2: %f" % lp2

		sys.exit(0)


	return lp

# CrossCat Marginal Likelihood
# Computes the marginal likelihood of the array of data in ccmat given all 
# possible partitionings of columns and rows of ccmat into views and categories.
# Goes through each partitioning, divides the data up and sequentially sends 
# that data and the priors to NGML, then sums these answers (they're log).
# 	Takes the data array ccmat; the prior mean, M0; the prior variance, V0; the 
# inverse-gamma hyperparameters A0 and B0; and the CRP concentration parameter, 
# alpha.
# 	Returns the log marginal likelohood.
def CCML(ccpart,ccmat,mu,r,nu,s,row_alpha,col_alpha):
	lp = []
	
	state = ccpart.states[1]

	# loop through the states
	for state in ccpart.states:
		all_cols = state['col_parts']
		all_rows = state['row_parts']

		K = max(all_cols)
				
		lp_temp = lcrp(all_cols,col_alpha)
		for view in range(K):
			row_part =  all_rows[view,:]
			lp_temp += lcrp(row_part,row_alpha)
			cols_view = np.nonzero(all_cols==view+1)[0]

			for col in cols_view:
				for cat in range(row_part.max()):
					X = ccmat[np.nonzero(row_part==cat+1)[0],col]
					lp_temp += NGML(X,mu,r,nu,s)

		lp.append(lp_temp);

	# return the normalized probabilities
	return lp-sp.misc.logsumexp(lp)

# Fixes the prior
def FixPriors(X_L,alpha,mu,s,r,nu):
	num_cols = len(X_L['column_partition']['assignments'])
	X_L['column_partition']['hypers']['alpha'] = alpha
	# print(new_X_L)
	for i in range(len(X_L['view_state'])):
		X_L['view_state'][i]['row_partition_model']['hypers']['alpha'] = alpha
	for i in range(num_cols):
		X_L['column_hypers'][i]['alpha'] = alpha
		X_L['column_hypers'][i]['mu']    = mu
		X_L['column_hypers'][i]['s']     = s
		X_L['column_hypers'][i]['r']     = r
		X_L['column_hypers'][i]['nu']    = nu

	return X_L

# Convert assignment vector to cohabitation matrix. A cohabitation matrix is an 
# N-by-N matrix where entry [i,j] = 1 is data points i and j belong to the same
# category and 0 otherwise. This function is used to match sampled states with
# enumerated states to compare the sampler with the enumerated answers.
def vectorToCHMat(col_partition):
	# print(col_partition)
	N = len(col_partition)
	
	chmat = np.zeros((N,N))
	for i in range(N):
		for j in range(N):
			if col_partition[i] == col_partition[j]:
				chmat[i,j] = 1
	return chmat

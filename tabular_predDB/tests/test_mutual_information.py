import numpy
import pylab as pl
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.inference_utils as iu
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.cython_code.State as State

import random
import math

import pdb

def ring(n=200):

	X = numpy.zeros((n,2))
	for i in range(n):
		angle = random.uniform(0,2*math.pi)
		distance = random.uniform(1,1.5)
		X[i,0] = math.cos(angle)*distance
		X[i,1] = math.sin(angle)*distance

	return X

def circle(n=200):

	X = numpy.zeros((n,2))
	for i in range(n):
		angle = random.uniform(0,2*math.pi)
		distance = random.uniform(0,1.5)
		X[i,0] = math.cos(angle)*distance
		X[i,1] = math.sin(angle)*distance

	return X

def square(n=200):

	X = numpy.zeros((n,2))
	for i in range(n):
		x = random.uniform(-1,1)
		y = random.uniform(-1,1)
		X[i,0] = x
		X[i,1] = y

	return X

def diamond(n=200):

	X = square(n=n)
	for i in range(n):
		angle = math.atan(X[i,1]/X[i,0])
		angle += math.pi/4 
		hyp = (X[i,0]**2.0+X[i,1]**2.0)**.5
		x = math.cos(angle)*hyp
		y = math.sin(angle)*hyp
		X[i,0] = x
		X[i,1] = y

	return X

def four_dots(n=200):
	X = numpy.zeros((n,2))
	nb = n/4
	mx = [ -1, 1, -1, 1]
	my = [ -1, -1, 1, 1]
	s = .25
	
	for i in range(n):
		n = random.randrange(4)
		x = random.normalvariate(mx[n], s)
		y = random.normalvariate(my[n], s)
		X[i,0] = x
		X[i,1] = y
		
	return X

def correlated(r,n=200):
	X = numpy.random.multivariate_normal([0,0], [[1, r],[r, 1]], n)
	return X

def sample_from_view(M_c, X_L, X_D, get_next_seed):
    
    view_col = X_L['column_partition']['assignments'][0]
    view_col2 = X_L['column_partition']['assignments'][1]

    same_view = True
    if view_col2 != view_col:
    	same_view = False

    view_state = X_L['view_state'][view_col]
    view_state2 = X_L['view_state'][view_col2]

    cluster_crps = numpy.exp(su.determine_cluster_crp_logps(view_state))
    cluster_crps2 = numpy.exp(su.determine_cluster_crp_logps(view_state2))

    assert( math.fabs(numpy.sum(cluster_crps) - 1) < .00000001 )

    samples = numpy.zeros((n,2))

    
    cluster_idx1 = numpy.nonzero(numpy.random.multinomial(1, cluster_crps))[0][0]
    cluster_model1 = su.create_cluster_model_from_X_L(M_c, X_L, view_col, cluster_idx1)

    if same_view:
    	cluster_idx2 = cluster_idx1
    	cluster_model2 = cluster_model1
    else:
    	cluster_idx2 = numpy.nonzero(numpy.random.multinomial(1, cluster_crps2))[0][0]
    	cluster_model2 = su.create_cluster_model_from_X_L(M_c, X_L, view_col2, cluster_idx2)

    component_model1 = cluster_model1[0]
    x = component_model1.get_draw(get_next_seed())

    component_model2 = cluster_model2[1]
    y = component_model2.get_draw(get_next_seed())
        
    return x, y

def sample_data_from_crosscat(M_c, X_Ls, X_Ds, get_next_seed, n):

	X = numpy.zeros((n,2))
	n_samples = len(X_Ls)
	
	for i in range(n):
		cc = random.randrange(n_samples)
		x, y = sample_from_view(M_c, X_Ls[cc], X_Ds[cc], get_next_seed)
		
		X[i,0] = x
		X[i,1] = y

	return X

def do_test(which_plot, max_plots, n, burn_in, cc_samples, which_test, correlation=0, do_plot=False):
	if which_test is "correlated":
		X = correlated(correlation, n=n)
	elif which_test is "square":
		X = square(n=n)
	elif which_test is "ring":
		X = ring(n=n)
	elif which_test is "circle":
		X = circle(n=n)
	elif which_test is "diamond":
		X = diamond(n=n)
	elif which_test is "blob":
		X = correlated(0.0, n=n)
	elif which_test is "dots":
		X = four_dots(n=n)
	elif which_test is "mixed":
		X = numpy.vstack((correlated(.95, n=n/2),correlated(0, n=n/2)))

	get_next_seed = lambda : random.randrange(32000)

	# Build a state
	M_c = du.gen_M_c_from_T(X.tolist())
	state = State.p_State(M_c, X.tolist())
	X_Ls = []
	X_Ds = []
	
	# collect crosscat samples
	for _ in range(cc_samples):
		state = State.p_State(M_c, X.tolist())
		state.transition(n_steps=burn_in)
		X_Ds.append(state.get_X_D())
		X_Ls.append(state.get_X_L())

	SX = sample_data_from_crosscat(M_c, X_Ls, X_Ds, get_next_seed, n)

	if do_plot:
		pl.subplot(2,max_plots,which_plot)
		pl.scatter(X[:,0],X[:,1],c='blue',alpha=.5)
		pl.title("Original data")
		pl.subplot(2,max_plots,max_plots+which_plot)
		pl.scatter(SX[:,0],SX[:,1],c='red',alpha=.5)
		pl.title("Sampled data")
		pl.show

	return M_c, X_Ls, X_Ds

def MI_test(n, burn_in, cc_samples, which_test, n_MI_samples=500, correlation=0):
	M_c, X_Ls, X_Ds = do_test(0, 0, n, burn_in, cc_samples, "correlated", correlation=correlation, do_plot=False)
	# query column 0 and 1
	MI, Linfoot = su.mutual_information(M_c, X_Ls, X_Ds, [(0,1)], n_samples=n_MI_samples)

	MI = numpy.mean(MI)
	Linfoot = numpy.mean(Linfoot)
	
	if which_test == "correlated":
		test_strn = "Test: correlation (%1.2f), N: %i, burn_in: %i, samples: %i, MI_samples: %i\n\tMI: %f, Linfoot %f" % (correlation, n, burn_in, cc_samples, n_MI_samples, MI, Linfoot)
	else:
		test_strn = "Test: %s, N: %i, burn_in: %i, samples: %i, MI_samples: %i\n\tMI: %f, Linfoot %f" % (which_test, n, burn_in, cc_samples, n_MI_samples, MI, Linfoot)
		

	print test_strn
	return test_strn

do_plot = False
n_mi_samples = 500

N = [10, 100, 1000] 

burn_in = 200
cc_samples = 10

print " "
for n in N:
	
	strn = MI_test(n, burn_in, cc_samples, "correlated", correlation=.3)
	strn = MI_test(n, burn_in, cc_samples, "correlated", correlation=.6)
	strn = MI_test(n, burn_in, cc_samples, "correlated", correlation=.9)
	strn = MI_test(n, burn_in, cc_samples, "ring")
	strn = MI_test(n, burn_in, cc_samples, "dots")
	strn = MI_test(n, burn_in, cc_samples, "mixed")



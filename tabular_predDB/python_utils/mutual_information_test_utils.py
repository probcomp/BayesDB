import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.cython_code.State as State
import random
import numpy

# Generates a num_rows by num_cols array of data with covariance matrix I^{num_cols}*corr
def generate_correlated_data(num_rows, num_cols, means, corr, seed=0):
	assert(corr <= 1 and corr >= 0)
	assert(num_cols == len(means))

	numpy.random.seed(seed=seed)

	mu = numpy.array(means)
	sigma = numpy.ones((num_cols,num_cols),dtype=float)*corr
	for i in range(num_cols):
		sigma[i,i] = 1 
	X = numpy.random.multivariate_normal(mu, sigma, num_rows)

	return X

def generate_correlated_state(num_rows, num_cols, num_views, num_clusters, mean_range, corr, seed=0):
	#

	assert(num_clusters <= num_rows)
	assert(num_views <= num_cols)
	T = numpy.zeros((num_rows, num_cols))

	random.seed(seed)
	numpy.random.seed(seed=seed)
	get_next_seed = lambda : random.randrange(2147483647)

	# generate an assignment of columns to views (uniform)
	cols_to_views = range(num_views)
	view_counts = numpy.ones(num_views, dtype=int)
	for i in range(num_views, num_cols):
		r = random.randrange(num_views)
		cols_to_views.append(r)
		view_counts[r] += 1

	random.shuffle(cols_to_views)

	assert(len(cols_to_views) == num_cols)
	assert(max(cols_to_views) == num_views-1)

	# for each view, generate an assignment of rows to num_clusters
	row_to_clusters = []
	cluster_counts = []
	for view in range(num_views):
		row_to_cluster = range(num_clusters)
		cluster_counts_i = numpy.ones(num_clusters,dtype=int)
		for i in range(num_clusters, num_rows):
			r = random.randrange(num_clusters)
			row_to_cluster.append(r)
			cluster_counts_i[r] += 1

		random.shuffle(row_to_cluster)

		assert(len(row_to_cluster) == num_rows)
		assert(max(row_to_cluster) == num_clusters-1)

		row_to_clusters.append(row_to_cluster)
		cluster_counts.append(cluster_counts_i)

	assert(len(row_to_clusters) == num_views)

	# generate the correlated data
	for view in range(num_views):
		for cluster in range(num_clusters):
			cell_cols = view_counts[view]
			cell_rows = cluster_counts[view][cluster]
			means = numpy.random.uniform(-mean_range/2.0,mean_range/2.0,cell_cols)
			X =  generate_correlated_data(cell_rows, cell_cols, means, corr, seed=get_next_seed())
			# get the indices of the columns in this view
			col_indices = numpy.nonzero(numpy.array(cols_to_views)==view)[0]
			# get the indices of the rows in this view and this cluster
			row_indices = numpy.nonzero(numpy.array(row_to_clusters[view])==cluster)[0]
			# insert the data
			for col in range(cell_cols):
				for row in range(cell_rows):
					r = row_indices[row]
					c = col_indices[col]
					T[r,c] = X[row,col]


	M_c = du.gen_M_c_from_T(T)
	M_r = du.gen_M_r_from_T(T)
	X_L, X_D = generate_X_L_and_X_D(T, M_c, cols_to_views, row_to_clusters, seed=get_next_seed())

	return  T, M_c, M_r, X_L, X_D, cols_to_views

def generate_X_L_and_X_D(T, M_c, cols_to_views, row_to_clusters, seed=0):
	state = State.p_State(M_c, T, SEED=seed)
	X_L = state.get_X_L()

	# insert assigment into X_L (this is not a valid X_L because the counts and 
	# suffstats will be wrong)
	X_L['column_partition']['assignments'] = cols_to_views
	state = State.p_State(M_c, T, X_L=X_L, X_D=row_to_clusters, SEED=seed)

	X_L = state.get_X_L()
	X_D = state.get_X_D()

	return X_L, X_D


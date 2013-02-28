# settings
N_samples = 1000
posterior_seed = 0
color_list = ['r', 'g', 'b', 'c', 'm', 'y']
marker_list = ['o', 'x', '<']

# setup for posterior sample drawing
random_state = numpy.random.RandomState(posterior_seed)
num_cols = T.shape[1]
view_state_list = p_State.get_view_state()
#
column_view_idx_lookup = dict()
for view_idx, view_state_i in enumerate(view_state_list):
    for column_idx in view_state_i['column_names']:
        column_view_idx_lookup[column_idx] = view_idx
# actually draw samples
sample_list = []
for sample_idx in range(N_samples):
    sample = sh.generate_sample(random_state, p_State, column_view_idx_lookup)
    sample_list.append(sample)

# plot samples
sample_arr = numpy.array(sample_list)
pylab.figure()
pylab.scatter(sample_arr[:,0], sample_arr[:,1])

# plot the latent state
which_view = 0
cluster_indices = X_D[which_view]
unique_cluster_indices = set(cluster_indices)
pylab.figure()
for cluster_idx in list(unique_cluster_indices):
    which_data_bool = numpy.array(cluster_indices) == cluster_idx
    which_data = T[which_data_bool]
    which_color = color_list[cluster_idx % len(color_list)]
    which_marker = marker_list[cluster_idx / len(color_list)]
    print which_color, which_marker
    pylab.scatter(which_data[:, 0], which_data[:, 1],
                  color=which_color, marker=which_marker)

# plot some derived info
which_view = 0
get_mus = lambda hypers_pair: (hypers_pair[0][3], hypers_pair[1][3]) 
cluster_hypers = sh.generate_view_cluster_means(p_State, which_view)
cluster_means = numpy.array(map(get_mus, cluster_hypers))
pylab.scatter(cluster_means[:, 0], cluster_means[:, 1],
              color='k', marker='D', linewidths=2)

print p_State.get_view_state()[0]['row_partition_model']['counts']

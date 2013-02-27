# setup for posterior sample drawing
posterior_seed = 0
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
N_samples = 1000
for sample_idx in range(N_samples):
    sample = sh.generate_sample(random_state, p_State, column_view_idx_lookup)
    sample_list.append(sample)

# plot
sample_arr = numpy.array(sample_list)
pylab.scatter(sample_arr[:,0], sample_arr[:,1])

# plot the latent state
which_view = 0
cluster_indices = X_D[which_view]
unique_cluster_indices = set(cluster_indices)
pylab.figure()
color_list = ['r', 'g', 'b', 'c', 'm', 'y']
marker_list = ['o', 'x', '<']
for cluster_idx in list(unique_cluster_indices):
    which_data_bool = numpy.array(cluster_indices) == cluster_idx
    which_data = T[which_data_bool]
    which_color = color_list[cluster_idx % len(color_list)]
    which_marker = marker_list[cluster_idx / len(color_list)]
    print which_color, which_marker
    pylab.scatter(which_data[:, 0], which_data[:, 1], color=which_color, marker=which_marker)
#
temp = sh.generate_view_cluster_means(p_State, 0)
temp = numpy.array([(el[0][3], el[1][3]) for el in temp])
pylab.scatter(temp[:, 0], temp[:, 1], color='k', marker='o')

print p_State.get_view_state()[0]['row_partition_model']['counts']

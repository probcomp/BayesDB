import argparse
#
import numpy
#
import tabular_predDB.analyze_2d.make_ring as make_ring
import tabular_predDB.analyze_2d.sampler_helpers as sh
import tabular_predDB.cython.State as State


# generate the data
N_datapoints = 1000
gen_seed = 0
gen_noise_scale = 0.1
ring_data = make_ring.create_ring_data(N_datapoints, gen_seed, 0, gen_noise_scale)
#
with open('ring_data.csv', 'w') as fh:
    array_as_string = '\n'.join(map(lambda row: ','.join(map(str, row)), ring_data))
    fh.write(array_as_string)
    # ring_data.tofile(fh, sep=',')

# prepare datastructures for inference
name_to_idx=dict()
idx_to_name=dict()
column_metadata_i = dict(
    modeltype='normal_inverse_gamma',
    value_to_code=dict(),
    code_to_value=dict()
    )
column_metadata = [column_metadata_i, column_metadata_i]
#
T = ring_data
M_c = dict(
    name_to_idx=name_to_idx,
    idx_to_name=idx_to_name,
    column_metadata=column_metadata,
)

# generate state, do transitions
p_State = State.p_State(M_c, T)
for idx in range(600):
    print "transitioning"
    p_State.transition()
#
X_D = p_State.get_X_D()
X_L = p_State.get_X_L()
print "X_D:", X_D
print "X_L:", X_L
for view_idx, view_state_i in enumerate(p_State.get_view_state()):
    print "view_state_i:", view_idx
    for key, value in view_state_i.iteritems():
        print key, value
    print

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
import pylab
pylab.scatter(sample_arr[:,0], sample_arr[:,1])
pylab.ion()
pylab.show()



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
    pylab.scatter(which_data[:, 0], which_data[:, 1], color=which_color, marker=which_marker)

temp = sh.generate_view_cluster_means(p_State, 0)
temp = numpy.array([(el[0][2], el[1][2]) for el in temp])
pylab.scatter(temp[:, 0], temp[:, 1], color='k', marker='o')

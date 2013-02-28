import argparse
#
import numpy
import pylab
pylab.ion()
pylab.show()
#
import tabular_predDB.analyze_2d.make_ring as make_ring
import tabular_predDB.analyze_2d.sampler_helpers as sh
import tabular_predDB.cython.State as State


# generative settings
N_datapoints = 1000
gen_seed = 0
gen_noise_scale = 0.1
data_filename = 'ring_data.csv'
#
# inference settings
N_transitions = 400
inference_seed = 1

# generate data
ring_data = make_ring.create_ring_data(
    N_datapoints, gen_seed, 0, gen_noise_scale)
#
row_to_string = lambda row: ','.join(map(str, row))
array_to_string = lambda array: '\n'.join(map(row_to_string, array))
with open(data_filename, 'w') as fh:
    array_as_string = array_to_string(ring_data)
    fh.write(array_as_string)

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
p_State = State.p_State(M_c, T, SEED=inference_seed)
for idx in range(N_transitions):
    print "transitioning: %s" % idx
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

execfile('posterior_analysis.py')

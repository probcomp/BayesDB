import argparse
#
import numpy
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.general_utils as gu
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.LocalEngine as LE
import tabular_predDB.cython_code.State as State


parser = argparse.ArgumentParser()
parser.add_argument('--gen_seed', type=int, default=0)
parser.add_argument('--num_clusters', type=int, default=20)
parser.add_argument('--num_rows', type=int, default=1000)
parser.add_argument('--num_cols', type=int, default=20)
parser.add_argument('--max_std', type=float, default=.001)
parser.add_argument('--n_steps', type=int, default=10)
#
args = parser.parse_args()
gen_seed = args.gen_seed
num_clusters = args.num_clusters
num_cols = args.num_cols
num_rows = args.num_rows
max_std = args.max_std
n_steps = args.n_steps


# one split for simplicity
num_splits = 1

# helper functions
extract_view_count = lambda X_L: len(X_L['view_state'])
extract_ith_cluster_count = lambda view_idx, X_L: len(X_L['view_state'][0]['row_partition_model']['counts'])
extract_0th_cluster_count = lambda X_L: extract_ith_cluster_count(0, X_L)
get_0th_view_dims = lambda X_L: (extract_0th_cluster_count(X_L), extract_view_count(X_L))
#
def get_generative_clustering(M_c, M_r, T, data_inverse_permutation_indices, gen_X_D):
    # assumes 1 view
    assert len(data_inverse_permutation_indices) == 1, "Can only work with 1 View"
    local_engine = LE.LocalEngine()
    #
    # initialize to generate an X_L to manipulate
    M_c, M_r, X_L, X_D = local_engine.initialize(M_c, M_r, T,
                                                 initialization='together')
    # manually constrcut state in in generative configuration
    state = State.p_State(M_c, T, X_L, gen_X_D)
    X_L = state.get_X_L()
    X_D = state.get_X_D()
    # run inference on hyperparameters to leave them in a reasonable state
    kernel_list = ('row_partition_hyperparameters',
                   'column_hyperparameters',
                   'column_partition_hyperparameter')
    X_L, X_D = local_engine.analyze(M_c, T, X_L, X_D, n_steps=1,
                                    kernel_list=kernel_list)
    #
    return X_L, X_D

# generate the data
T, M_r, M_c, data_inverse_permutation_indices = \
    du.gen_factorial_data_objects(gen_seed, num_clusters,
                               num_cols, num_rows, num_splits,
                               max_mean=10, max_std=1,
                               send_data_inverse_permutation_indices=True)
T_array = numpy.array(T)[data_inverse_permutation_indices[0]]
T = T_array.tolist()
# pu.plot_T(T_array, M_c, filename=None, dir='', close=False)
#
gen_X_D = [numpy.repeat(range(num_clusters), (num_rows / num_clusters))]
X_L, X_D = get_generative_clustering(M_c, M_c, T,
                                     data_inverse_permutation_indices,
                                     gen_X_D)

# run some transitions
all_kernels = State.transition_name_to_method_name_and_args.keys()
local_engine = LE.LocalEngine()
for which_kernel in all_kernels:
    # set alphas to something unlikely to split out elements
    X_L['view_state'][0]['row_partition_model']['hypers']['alpha'] = 0.01
    X_L['column_partition']['hypers']['alpha'] = 0.01
    kernel_list = (which_kernel,)
    start_dims = get_0th_view_dims(X_L)
    timer_message = 'n_steps=%s of %s kernel' % (n_steps, which_kernel)
    with gu.Timer(timer_message) as timer:
        X_L, X_D = local_engine.analyze(M_c, T, X_L, X_D, n_steps=n_steps, kernel_list=kernel_list)
    end_dims = get_0th_view_dims(X_L)
    print 'start_dims, end_dims: %s, %s' % (start_dims, end_dims)
    # pu.plot_views(T_array, X_D, X_L, M_c)

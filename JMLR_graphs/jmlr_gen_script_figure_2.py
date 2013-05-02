import argparse
import datetime
#
import pylab
import numpy
#
import tabular_predDB.cython_code.State as State
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.general_utils as gu


# parse input
parser = argparse.ArgumentParser()
parser.add_argument('--gen_seed', default=0, type=int)
parser.add_argument('--inf_seed', default=0, type=int)
parser.add_argument('--num_clusters', default=10, type=int)
parser.add_argument('--num_cols', default=100, type=int)
parser.add_argument('--num_rows', default=300, type=int)
parser.add_argument('--num_views', default=10, type=int)
parser.add_argument('--num_iters', default=500, type=int)
parser.add_argument('--max_mean', default=10, type=float)
parser.add_argument('--max_std', default=30, type=float)
parser.add_argument('--N_GRID', default=31, type=int)
args = parser.parse_args()
#
gen_seed = args.gen_seed
inf_seed = args.inf_seed
num_clusters = args.num_clusters
num_cols = args.num_cols
num_rows = args.num_rows
num_views = args.num_views
num_iters = args.num_iters
max_mean = args.max_mean
max_std = args.max_std
N_GRID = args.N_GRID


str_args = (num_views, gen_seed, inf_seed)
save_filename_prefix = 'num_views_%s_gen_seed_%s_inf_seed_%s' % str_args


# helper functions
def get_num_views(p_State):
    return len(p_State.get_X_D())
#
def get_assignments(p_State):
    return p_State.get_X_L()['column_partition']['assignments']
#
def append_accumulated(in_list, to_append):
    last = 0.
    if len(in_list) != 0:
        last = in_list[-1]
    in_list.append(last + to_append)
    return in_list


# create the data
T, M_r, M_c, data_inverse_permutation_indices = \
    du.gen_factorial_data_objects(
    gen_seed, num_clusters,
    num_cols, num_rows, num_views,
    max_mean=max_mean, max_std=max_std,
    send_data_inverse_permutation_indices=True,
    )

if False:
    import tabular_predDB.python_utils.plot_utils as pu
    T_array = numpy.array(T)
    fake_X_D = data_inverse_permutation_indices
    num_views = len(data_inverse_permutation_indices)
    num_cols_per_view = num_cols / num_views
    assignments = numpy.repeat(range(num_views), num_cols_per_view)
    fake_X_L = dict(column_partition=dict(assignments=assignments))
    pu.plot_views(T_array, fake_X_D, fake_X_L)

non_column_partition_assignments = [
    'column_partition_hyperparameter',
    'column_hyperparameters',
    'row_partition_hyperparameters',
    'row_partition_assignments',
]
valid_initializers = set(["together", "from_the_prior", "apart"])
initialization = 'from_the_prior'
# create the state
p_State = State.p_State(M_c, T, N_GRID=N_GRID, SEED=inf_seed,
                        initialization=initialization)
before_after_list = []
for iter_idx in range(num_iters):
    timer_str = '%s: iter_idx=%s' % (initialization, iter_idx)
    print '%s: %s' % (datetime.datetime.now(), timer_str)
    # transition just the first column
    before_X_L = p_State.get_X_L()
    before_assignment = get_assignments(p_State)[0]
    p_State.transition(which_transitions=('column_partition_assignments',),
                       c=(0,))
    after_X_L = p_State.get_X_L()
    after_assignment = get_assignments(p_State)[0]
    if before_assignment != after_assignment:
        print 'got column 0 transtition on iter idx %s' % iter_idx
        before_after_list.append((before_X_L, after_X_L))
    # transition all other columns
    p_State.transition(which_transitions=('column_partition_assignments',),
                       c=range(1, num_cols))
    # do all other transition types
    p_State.transition(which_transitions=non_column_partition_assignments)

# FIXME: will want to keep longitudinal records of column hypers for column 0
#        to say where in its range it was when transition occurred

import argparse
#
import pylab
import numpy
#
import tabular_predDB.cython.State as State
import tabular_predDB.python_utils.data_utils as du


# parse input
parser = argparse.ArgumentParser()
parser.add_argument('--gen_seed', default=0, type=int)
parser.add_argument('--inf_seed', default=0, type=int)
parser.add_argument('--num_clusters', default=4, type=int)
parser.add_argument('--num_cols', default=4, type=int)
parser.add_argument('--num_rows', default=2000, type=int)
parser.add_argument('--num_splits', default=1, type=int)
parser.add_argument('--max_mean', default=10, type=float)
parser.add_argument('--max_std', default=0.3, type=float)
parser.add_argument('--num_transitions', default=100, type=int)
parser.add_argument('--N_GRID', default=31, type=int)
args = parser.parse_args()
#
gen_seed = args.gen_seed
inf_seed = args.inf_seed
num_clusters = args.num_clusters
num_cols = args.num_cols
num_rows = args.num_rows
num_splits = args.num_splits
max_mean = args.max_mean
max_std = args.max_std
num_transitions = args.num_transitions
N_GRID = args.N_GRID

p_multinomial = .5
random_state = numpy.random.RandomState(gen_seed)
is_multinomial = random_state.binomial(1, p_multinomial, num_cols)
multinomial_column_indices = numpy.nonzero(is_multinomial)[0]

# create the data
if True:
    T, M_r, M_c = du.gen_factorial_data_objects(
        gen_seed, num_clusters,
        num_cols, num_rows, num_splits,
        max_mean=max_mean, max_std=max_std,
        )
else:
    with open('SynData2.csv') as fh:
        import numpy
        import csv
        T = numpy.array([
                row for row in csv.reader(fh)
                ], dtype=float).tolist()
        M_r = du.gen_M_r_from_T(T)
        M_c = du.gen_M_c_from_T(T)

T = du.discretize_data(T, multinomial_column_indices)
T, M_c = du.convert_columns_to_multinomial(T, M_c,
                                           multinomial_column_indices)

# create the state
p_State = State.p_State(M_c, T, N_GRID=N_GRID, SEED=inf_seed)
p_State.plot_T(filename='T')
print M_c
print numpy.array(T)
print p_State
print "multinomial_column_indices: %s" % str(multinomial_column_indices)

def summarize_p_State(p_State):
    counts = [
        view_state['row_partition_model']['counts']
        for view_state in p_State.get_X_L()['view_state']
        ]
    format_list = '; '.join([
            "s.num_views: %s",
            "cluster counts: %s",
            "s.column_crp_score: %.3f",
            "s.data_score: %.1f",
            "s.score:%.1f",
            ])
    values_tuple = (
        p_State.get_num_views(),
        str(counts),
        p_State.get_column_crp_score(),
        p_State.get_data_score(),
        p_State.get_marginal_logp(),
        )
    print format_list % values_tuple    
    if not numpy.isfinite(p_State.get_data_score()):
        print "bad data score"
        print p_State

# transition the sampler
for transition_idx in range(num_transitions):
    print "transition #: %s" % transition_idx
    p_State.transition()
    summarize_p_State(p_State)
    iter_idx = None
    pkl_filename = 'last_iter_pickled_state.pkl.gz'
    plot_filename = 'last_iter_X_D'
    if transition_idx % 10 == 0:
        plot_filename = 'iter_%s_X_D' % transition_idx
        pkl_filename = 'iter_%s_pickled_state.pkl.gz' % transition_idx
    p_State.save(filename=pkl_filename, M_c=M_c, T=T)
    p_State.plot(filename=plot_filename)

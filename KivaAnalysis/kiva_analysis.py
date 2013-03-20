import argparse
import csv
#
import pylab
import numpy
#
import tabular_predDB.cython.State as State
import tabular_predDB.python_utils.data_utils as du


# parse input
parser = argparse.ArgumentParser()
parser.add_argument('--filename', default='testdata_kiva100files_mod.csv',
                    type=str)
parser.add_argument('--inf_seed', default=0, type=int)
parser.add_argument('--num_transitions', default=100, type=int)
parser.add_argument('--N_GRID', default=31, type=int)
parser.add_argument('--max_rows', default=4000, type=int)

args = parser.parse_args([])
#
filename = args.filename
inf_seed = args.inf_seed
num_transitions = args.num_transitions
N_GRID = args.N_GRID
max_rows = args.max_rows


continuous_labels = set([
        'Lender Country GDP Score', 'Lender Join Date', 'Lender Loan count',
        'Lender Invitee Count', 'Borrower Country GDP Score',
        'Number of Borrowers', 'Funded Amount', 'Loan Amount'
        ])
multinomial_labels = set([
        'Lender Country Label', 'Lender Occupation Label', 'Lender URL Flag',
        'Borrower Country Label', 'Field Partner ID', 'Loan ID',
        'Loan Sector Label', 'Loan Status Label'
        ])
header = None
T, M_r, M_c = None, None, None
num_cols = 100
with open(filename) as fh:
    csv_reader = csv.reader(fh)
    header = csv_reader.next()[:num_cols]
    T = numpy.array([
            row[:num_cols] for row in csv_reader
            ], dtype=float).tolist()
    num_rows = len(T)
    if num_rows > max_rows:
        random_state = numpy.random.RandomState(inf_seed)
        which_rows = random_state.permutation(xrange(num_rows))[:max_rows]
        T = [T[which_row] for which_row in which_rows]
    M_r = du.gen_M_r_from_T(T)
    M_c = du.gen_M_c_from_T(T)

is_multinomial = [label in multinomial_labels for label in header]
multinomial_column_indices = numpy.nonzero(is_multinomial)[0]
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

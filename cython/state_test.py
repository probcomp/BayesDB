import argparse
#
import tabular_predDB.cython.State as State
import tabular_predDB.cython.gen_data as gen_data


# parse input
parser = argparse.ArgumentParser()
parser.add_argument('--gen_seed', default=0, type=int)
parser.add_argument('--num_clusters', default=4, type=int)
parser.add_argument('--num_cols', default=8, type=int)
parser.add_argument('--num_rows', default=1000, type=int)
parser.add_argument('--num_splits', default=2, type=int)
parser.add_argument('--max_mean', default=10, type=float)
parser.add_argument('--max_std', default=0.3, type=float)
args = parser.parse_args()
#
gen_seed = args.gen_seed
num_clusters = args.num_clusters
num_cols = args.num_cols
num_rows = args.num_rows
num_splits = args.num_splits
max_mean = args.max_mean
max_std = args.max_std

# create the data
data, inverse_permutation_indices_list = \
    gen_data.gen_factorial_data(gen_seed, num_clusters,
                                num_cols, num_rows, num_splits,
                                max_mean, max_std)
with open('data.csv', 'w') as fh:
    data.tofile(fh, sep=',')

## need to actually generate clusters, this is all one cluster
global_row_indices = range(num_rows)
global_col_indices = range(num_cols)


# "symmetric_dirichlet_discrete", "normal_inverse_gamma"

column_types = ["normal_inverse_gamma" for global_col_idx in global_col_indices]
event_counts = [0 for global_col_idx in global_col_indices]
p_State = State.p_State(data, global_row_indices, global_col_indices, N_GRID=31, SEED=0)
print "p_State.get_marginal_logp():", p_State.get_marginal_logp()
for idx in range(3):
    print "transitioning"
    p_State.transition()
    print "p_State.get_column_groups():", p_State.get_column_groups()
    print "p_State.get_column_hypers():", p_State.get_column_hypers()
    print "p_State.get_column_partition():", p_State.get_column_partition()
    print "p_State.get_marginal_logp():", p_State.get_marginal_logp()
    for view_idx, view_state_i in enumerate(p_State.get_view_state()):
        print "view_state_i:", view_idx, view_state_i
X_D = p_State.get_X_D()
X_L = p_State.get_X_L()

print "X_D:", X_D
print "X_L:", X_L

constructor_args = State.transform_latent_state_to_constructor_args(X_L, X_D)
p_State_2 = State.p_State(data, **constructor_args)
X_D_prime = p_State_2.get_X_D()
X_L_prime = p_State_2.get_X_L()

print "X_D_prime:", X_D_prime
print "X_L_prime:", X_L_prime

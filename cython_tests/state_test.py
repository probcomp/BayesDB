import sys
import argparse
#
import numpy
#
import State

def gen_data(gen_seed, num_clusters, num_cols, num_rows, max_mean=10, max_std=1):
    n_grid = 11
    mu_grid = numpy.linspace(-max_mean, max_mean, n_grid)
    sigma_grid = 10 ** numpy.linspace(-1, numpy.log10(max_std), n_grid)
    num_rows_per_cluster = num_rows / num_clusters
    zs = numpy.repeat(range(num_clusters), num_rows_per_cluster)
    #
    random_state = numpy.random.RandomState(gen_seed)
    #
    which_mus = random_state.randint(len(mu_grid), size=(num_clusters,num_cols))
    which_sigmas = random_state.randint(len(sigma_grid), size=(num_clusters,num_cols))
    mus = mu_grid[which_mus]
    sigmas = sigma_grid[which_sigmas]
    clusters = []
    for row_mus, row_sigmas in zip(mus, sigmas):
        cluster_columns = []
        for mu, sigma in zip(row_mus, row_sigmas):
            cluster_column = random_state.normal(mu, sigma, num_rows_per_cluster)
            cluster_columns.append(cluster_column)
        cluster = numpy.vstack(cluster_columns).T
        clusters.append(cluster)
    xs = numpy.vstack(clusters)
    return xs, zs

def gen_factorial_data(gen_seed, num_clusters, num_cols, num_rows, num_splits,
                       max_mean=10, max_std=1):
    random_state = numpy.random.RandomState(gen_seed)
    data_list = []
    inverse_permutation_indices_list = []
    for data_idx in xrange(num_splits):
        data_i, zs_i = gen_data(
            gen_seed=random_state.randint(sys.maxint),
            num_clusters=num_clusters,
            num_cols=num_cols/num_splits,
            num_rows=num_rows,
            )
        permutation_indices = numpy.random.permutation(xrange(num_rows))
        inverse_permutation_indices = numpy.argsort(permutation_indices)
        inverse_permutation_indices_list.append(inverse_permutation_indices)
        data_list.append(numpy.array(data_i)[permutation_indices])
    data = numpy.hstack(data_list)
    return data, inverse_permutation_indices_list

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

data, inverse_permutation_indices_list = \
    gen_factorial_data(gen_seed, num_clusters, num_cols, num_rows, num_splits,
                       max_mean, max_std)

with open('data.csv', 'w') as fh:
    data.tofile(fh, sep=',')

## need to actually generate clusters, this is all one cluster
global_row_indices = range(num_rows)
global_col_indices = range(num_cols)

p_State = State.p_State(data, global_row_indices, global_col_indices, 31, 0)
print "p_State.get_marginal_logp():", p_State.get_marginal_logp()
for idx in range(100):
    print "transitioning"
    p_State.transition()
    print p_State.get_column_groups()
    #
    print "p_State.get_marginal_logp():", p_State.get_marginal_logp()

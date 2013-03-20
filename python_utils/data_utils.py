import sys
#
import numpy


def get_ith_ordering(in_list, i):
    temp_list = [in_list[j::(i+1)][:] for j in range(i+1)]
    return [el for sub_list in temp_list for el in sub_list]

def gen_data(gen_seed, num_clusters,
             num_cols, num_rows, max_mean=10, max_std=1):
    n_grid = 11
    mu_grid = numpy.linspace(-max_mean, max_mean, n_grid)
    sigma_grid = 10 ** numpy.linspace(-1, numpy.log10(max_std), n_grid)
    num_rows_per_cluster = num_rows / num_clusters
    zs = numpy.repeat(range(num_clusters), num_rows_per_cluster)
    #
    random_state = numpy.random.RandomState(gen_seed)
    #
    data_size = (num_clusters,num_cols)
    which_mus = random_state.randint(len(mu_grid), size=data_size)
    which_sigmas = random_state.randint(len(sigma_grid), size=data_size)
    mus = mu_grid[which_mus]
    sigmas = sigma_grid[which_sigmas]
    clusters = []
    for row_mus, row_sigmas in zip(mus, sigmas):
        cluster_columns = []
        for mu, sigma in zip(row_mus, row_sigmas):
            cluster_column = random_state.normal(mu, sigma,
                                                 num_rows_per_cluster)
            cluster_columns.append(cluster_column)
        cluster = numpy.vstack(cluster_columns).T
        clusters.append(cluster)
    xs = numpy.vstack(clusters)
    return xs, zs

def gen_factorial_data(gen_seed, num_clusters,
                       num_cols, num_rows, num_splits,
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
            max_mean=max_mean,
            max_std=max_std,
            )
        permutation_indices = numpy.random.permutation(xrange(num_rows))
        # permutation_indices = get_ith_ordering(range(num_rows), data_idx)
        inverse_permutation_indices = numpy.argsort(permutation_indices)
        inverse_permutation_indices_list.append(inverse_permutation_indices)
        data_list.append(numpy.array(data_i)[permutation_indices])
    data = numpy.hstack(data_list)
    return data, inverse_permutation_indices_list

def gen_M_r_from_T(T):
    num_rows = len(T)
    num_cols = len(T[0])
    #
    name_to_idx = dict(zip(map(str, range(num_rows)), range(num_rows)))
    idx_to_name = dict(zip(map(str, range(num_rows)), range(num_rows)))
    M_r = dict(name_to_idx=name_to_idx, idx_to_name=idx_to_name)
    return M_r

def gen_M_c_from_T(T):
    num_rows = len(T)
    num_cols = len(T[0])
    #
    gen_continuous_metadata = lambda: dict(modeltype="normal_inverse_gamma",
                                           value_to_code=dict(),
                                           code_to_value=dict())
    column_metadata = [
        gen_continuous_metadata()
        for col_idx in range(num_cols)
        ]
    name_to_idx = dict(zip(map(str, range(num_cols)),range(num_cols)))
    idx_to_name = dict(zip(map(str, range(num_cols)),range(num_cols)))
    M_c = dict(
        name_to_idx=name_to_idx,
        idx_to_name=idx_to_name,
        column_metadata=column_metadata,
        )
    return M_c

def gen_factorial_data_objects(gen_seed, num_clusters,
                               num_cols, num_rows, num_splits,
                               max_mean=10, max_std=1):
    T, data_inverse_permutation_indices = gen_factorial_data(
        gen_seed, num_clusters,
        num_cols, num_rows, num_splits, max_mean, max_std)
    T  = T.tolist()
    M_r = gen_M_r_from_T(T)
    M_c = gen_M_c_from_T(T)
    return T, M_r, M_c

def discretize_data(T, discretize_indices):
    T_array = numpy.array(T)
    discretize_indices = numpy.array(discretize_indices)
    T_array[:, discretize_indices] = \
        numpy.array(T_array[:, discretize_indices], dtype=int)
    return T_array.tolist()

def convert_columns_to_multinomial(T, M_c, multinomial_indices):
    multinomial_indices = numpy.array(multinomial_indices)
    modeltype = 'symmetric_dirichlet_discrete'
    T_array = numpy.array(T)
    for multinomial_idx in multinomial_indices:
        multinomial_column = T_array[:, multinomial_idx]
        multinomial_values = list(set(multinomial_column))
        K = len(multinomial_values)
        code_to_value = dict(zip(range(K), multinomial_values))
        value_to_code = dict(zip(multinomial_values, range(K)))
        multinomial_column_metadata = M_c['column_metadata'][multinomial_idx]
        multinomial_column_metadata['modeltype'] = modeltype
        multinomial_column_metadata['code_to_value'] = code_to_value
        multinomial_column_metadata['value_to_code'] = value_to_code
    return T, M_c

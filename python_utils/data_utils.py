import sys
import csv
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

def gen_continuous_metadata(column_data):
    return dict(
        modeltype="normal_inverse_gamma",
        value_to_code=dict(),
        code_to_value=dict(),
        )

def gen_multinomial_metadata(column_data):
    num_rows = len(column_data)
    unique_codes = list(set(column_data))
    values = range(len(unique_codes))
    value_to_code = dict(zip(values, unique_codes))
    code_to_value = dict(zip(unique_codes, values))
    return dict(
        modeltype="symmetric_dirichlet_discrete",
        value_to_code=value_to_code,
        code_to_value=code_to_value,
        )

metadata_generator_lookup = dict(
    continuous=gen_continuous_metadata,
    multinomial=gen_multinomial_metadata,
)

def gen_M_c_from_T(T, cctypes=None, colnames=None):
    num_rows = len(T)
    num_cols = len(T[0])
    if cctypes is None:
        cctypes = ['continuous'] * num_cols
    if colnames is None:
        colnames = range(num_cols)
    #
    T_array_transpose = numpy.array(T).T
    column_metadata = []
    for cctype, column_data in zip(cctypes, T_array_transpose):
        metadata_generator = metadata_generator_lookup[cctype]
        metadata = metadata_generator(column_data)
        column_metadata.append(metadata)
    name_to_idx = dict(zip(colnames, range(num_cols)))
    idx_to_name = dict(zip(map(str, range(num_cols)), colnames))
    M_c = dict(
        name_to_idx=name_to_idx,
        idx_to_name=idx_to_name,
        column_metadata=column_metadata,
        )
    return M_c

def gen_M_c_from_T_with_colnames(T, colnames):
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
    name_to_idx = dict(zip(colnames, range(num_cols)))
    idx_to_name = dict(zip(map(str, range(num_cols)),colnames))
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
        multinomial_column = multinomial_column[~numpy.isnan(multinomial_column)]
        multinomial_values = list(set(multinomial_column))
        K = len(multinomial_values)
        code_to_value = dict(zip(range(K), multinomial_values))
        value_to_code = dict(zip(multinomial_values, range(K)))
        multinomial_column_metadata = M_c['column_metadata'][multinomial_idx]
        multinomial_column_metadata['modeltype'] = modeltype
        multinomial_column_metadata['code_to_value'] = code_to_value
        multinomial_column_metadata['value_to_code'] = value_to_code
    return T, M_c

def all_continuous_from_file(filename, max_rows=None, gen_seed=0, has_header=True):
    header = None
    T, M_r, M_c = None, None, None
    with open(filename) as fh:
        csv_reader = csv.reader(fh)
        if has_header:
            header = csv_reader.next()
        T = numpy.array([
                row for row in csv_reader
                ], dtype=float).tolist()
        num_rows = len(T)
        if (max_rows is not None) and (num_rows > max_rows):
            random_state = numpy.random.RandomState(gen_seed)
            which_rows = random_state.permutation(xrange(num_rows))
            which_rows = which_rows[:max_rows]
            T = [T[which_row] for which_row in which_rows]
        M_r = gen_M_r_from_T(T)
        M_c = gen_M_c_from_T(T)
    return T, M_r, M_c, header

def continuous_or_ignore_from_file_with_colnames(filename, cctypes, max_rows=None, gen_seed=0):
    header = None
    T, M_r, M_c = None, None, None
    colmask = map(lambda x: 1 if x != 'ignore' else 0, cctypes)
    with open(filename) as fh:
        csv_reader = csv.reader(fh)
        header = csv_reader.next()
        T = numpy.array([
                [col for col, flag in zip(row, colmask) if flag] for row in csv_reader
                ], dtype=float).tolist()
        num_rows = len(T)
        if (max_rows is not None) and (num_rows > max_rows):
            random_state = numpy.random.RandomState(gen_seed)
            which_rows = random_state.permutation(xrange(num_rows))
            which_rows = which_rows[:max_rows]
            T = [T[which_row] for which_row in which_rows]
        M_r = gen_M_r_from_T(T)
        M_c = gen_M_c_from_T_with_colnames(T, [col for col, flag in zip(header, colmask) if flag])
    return T, M_r, M_c, header

cast_func_lookup = dict(
    continuous=float,
    multinomial=str,
    )
def read_data_objects(filename, max_rows=None, gen_seed=0,
                      cctypes=None, colnames=None):
    # FIXME: why both accept colnames argument and read header?
    header, rows = read_csv(filename, has_header=True)
    if cctypes is None:
        cctypes = ['continuous'] * len(header)
    keep_col_indices = numpy.nonzero(numpy.array(cctypes)!='ignore')[0]
    # remove ignore columns
    cctypes = numpy.array(cctypes)[keep_col_indices]
    header = numpy.array(header)[keep_col_indices]
    T_uncast_array = numpy.array(rows)[:, keep_col_indices]
    # remove excess rows
    num_rows = len(T_uncast_array)
    if (max_rows is not None) and (num_rows > max_rows):
        random_state = numpy.random.RandomState(gen_seed)
        which_rows = random_state.permutation(xrange(num_rows))
        which_rows = which_rows[:max_rows]
        T_uncast_array = T_uncast_array[which_rows]
    # cast to appropriate type
    T = []
    for uncast_row in T_uncast_array:
        cast_row = []
        for cctype, uncast_element in zip(cctypes, uncast_row):
            cast_func = cast_func_lookup[cctype]
            cast_element = cast_func(uncast_element)
            cast_row.append(cast_element)
        T.append(cast_row)
    M_r = gen_M_r_from_T(T)
    M_c = gen_M_c_from_T(T, cctypes, colnames)
    return T, M_r, M_c, header

def get_can_cast_to_float(column_data):
    can_cast = True
    try:
        [float(datum) for datum in column_data]
    except ValueError, e:
        can_cast = False
    return can_cast
    
def guess_column_type(column_data, count_cutoff=20, ratio_cutoff=0.02):
    num_distinct = len(set(column_data))
    num_data = len(column_data)
    distinct_ratio = float(num_distinct) / num_data
    above_count_cutoff = num_distinct > count_cutoff
    above_ratio_cutoff = distinct_ratio > ratio_cutoff
    can_cast = get_can_cast_to_float(column_data)
    if above_count_cutoff and above_ratio_cutoff and can_cast:
        column_type = 'continuous'
    else:
        column_type = 'multinomial'
    return column_type

def read_csv(filename, has_header=True):
    with open(filename) as fh:
        csv_reader = csv.reader(fh)
        header = None
        if has_header:
            header = csv_reader.next()
        rows = [row for row in csv_reader]
    return header, rows

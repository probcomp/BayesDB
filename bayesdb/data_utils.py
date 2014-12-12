#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import sys
import csv
import copy
import pandas
import re
import numpy
import json
import prettytable
from math import pi

import utils


def get_ith_ordering(in_list, i):
    temp_list = [in_list[j::(i+1)][:] for j in range(i+1)]
    return [el for sub_list in temp_list for el in sub_list]


def gen_data(gen_seed, num_clusters, num_cols, num_rows, max_mean_per_category=10, max_std=1,
             max_mean=None):
    if max_mean is None:
        max_mean = max_mean_per_category * num_clusters
    n_grid = 11
    mu_grid = numpy.linspace(-max_mean, max_mean, n_grid)
    sigma_grid = 10 ** numpy.linspace(-1, numpy.log10(max_std), n_grid)
    num_rows_per_cluster = num_rows / num_clusters
    zs = numpy.repeat(range(num_clusters), num_rows_per_cluster)
    #
    random_state = numpy.random.RandomState(gen_seed)
    #
    data_size = (num_clusters, num_cols)
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


def gen_factorial_data(gen_seed, num_clusters, num_cols, num_rows, num_splits,
                       max_mean_per_category=10, max_std=1, max_mean=None):
    random_state = numpy.random.RandomState(gen_seed)
    data_list = []
    inverse_permutation_indices_list = []
    for data_idx in xrange(num_splits):
        data_i, zs_i = gen_data(
            gen_seed=random_state.randint(sys.maxint),
            num_clusters=num_clusters,
            num_cols=num_cols/num_splits,
            num_rows=num_rows,
            max_mean_per_category=max_mean_per_category,
            max_std=max_std,
            max_mean=max_mean
            )
        permutation_indices = random_state.permutation(xrange(num_rows))
        # permutation_indices = get_ith_ordering(range(num_rows), data_idx)
        inverse_permutation_indices = numpy.argsort(permutation_indices)
        inverse_permutation_indices_list.append(inverse_permutation_indices)
        data_list.append(numpy.array(data_i)[permutation_indices])
    data = numpy.hstack(data_list)
    return data, inverse_permutation_indices_list


def gen_raw_T_full_from_T_full(T_full, M_c):
    """
    engine.upgrade_btables needs a way to go from T to raw_T_full for tables
    saved without a metadata_full file. This function takes T and M_c
    and reconstructs the raw data list.
    """
    raw_T_full = T_full
    for row_idx, row_data in enumerate(T_full):
        for col_idx, code in enumerate(row_data):
            code = T_full[row_idx][col_idx]
            raw_T_full[row_idx][col_idx] = str(convert_code_to_value(M_c, col_idx, code))
    return raw_T_full


def gen_M_r_from_T(T):
    num_rows = len(T)
    num_cols = len(T[0])
    #
    name_to_idx = dict(zip(map(str, range(num_rows)), range(num_rows)))
    idx_to_name = dict(zip(map(str, range(num_rows)), range(num_rows)))
    M_r = dict(name_to_idx=name_to_idx, idx_to_name=idx_to_name)
    return M_r


def gen_ignore_metadata(column_data, parameters=None):
    ret = gen_categorical_metadata(column_data, parameters)
    ret['modeltype'] = 'ignore'
    ret['parameters'] = None
    return ret


def gen_numerical_metadata(column_data, parameters=None):
    res = dict(
        modeltype="normal_inverse_gamma",
        value_to_code=dict(),
        code_to_value=dict(),
        parameters=None
    )
    return res


def gen_cyclic_metadata(column_data, parameters=None):

    data_min = min(map(float, column_data))
    data_max = max(map(float, column_data))

    if not parameters:
        parameters = dict(min=data_min, max=data_max)
    else:
        if 'min' not in parameters or 'max' not in parameters:
            raise utils.BayesDBError("Error: cyclic columns require (min, max) parameters."
                                     % str(value))
        else:
            param_min = float(parameters['min'])
            param_max = float(parameters['max'])
            if data_min < param_min:
                raise utils.BayesDBError("Error: cyclic contains data less than specified "
                                         "minimum %f" % param_min)
            elif data_max > param_max:
                raise utils.BayesDBError("Error: cyclic contains data greater than specified "
                                         "maximum %f" % param_max)
            else:
                parameters = dict(min=param_min, max=param_max)

    return dict(
        modeltype="vonmises",
        value_to_code=dict(),
        code_to_value=dict(),
        parameters=parameters
        )


def gen_categorical_metadata(column_data, parameters=None):
    def get_is_not_nan(el):
        if isinstance(el, str):
            return el.upper() != 'NAN'
        else:
            return True
    # get_is_not_nan = lambda el: el.upper() != 'NAN'
    #
    unique_codes = list(set(column_data))
    unique_codes = filter(get_is_not_nan, unique_codes)
    #
    values = range(len(unique_codes))
    value_to_code = dict(zip(values, unique_codes))
    code_to_value = dict(zip(unique_codes, values))

    # Set cardinality = number of distinct values if not set, otherwise check
    # that cardinality parameter is >= the number of distinct values.
    n_codes = len(unique_codes)
    if not parameters:
        parameters = dict(cardinality=n_codes)
    else:
        parameters['cardinality'] = int(parameters['cardinality'])
        if n_codes > parameters['cardinality']:
            raise utils.BayesDBError("Error: categorical contains more distinct values than "
                                     "specified cardinality %i" % parameters['cardinality'])

    ret = dict(
        modeltype="symmetric_dirichlet_discrete",
        value_to_code=value_to_code,
        code_to_value=code_to_value,
        parameters=parameters
    )

    return ret

metadata_generator_lookup = dict(
    numerical=gen_numerical_metadata,
    cyclic=gen_cyclic_metadata,
    categorical=gen_categorical_metadata,
    ignore=gen_ignore_metadata,
    key=gen_ignore_metadata,
)


def gen_M_c_from_T(T, cctypes=None, colnames=None, parameters=None, codebook=None):
    num_rows = len(T)
    num_cols = len(T[0])
    if cctypes is None:
        cctypes = ['numerical'] * num_cols
    if colnames is None:
        colnames = range(num_cols)
    if parameters is None:
        parameters = [None] * num_cols
    #
    T_array_transpose = numpy.array(T).T
    column_metadata = []
    for cctype, column_data, params in zip(cctypes, T_array_transpose, parameters):
        metadata_generator = metadata_generator_lookup[cctype]
        metadata = metadata_generator(column_data, params)
        column_metadata.append(metadata)

    column_codebook = []
    for col_idx, colname in enumerate(colnames):
        if codebook and colname in codebook:
            colname_codebook = codebook[colname]

            # update column metadata with value maps
            if colname_codebook['value_map'].upper() != 'NAN':
                if column_metadata[col_idx]['modeltype'] != 'symmetric_dirichlet_discrete':
                    raise utils.BayesDBError('Value map specified for non-categorical column({})').format(colname)

                try:
                    colvm = json.loads(colname_codebook['value_map'])
                    codes = colvm.keys()
                    values = colvm.values()
                    column_metadata[col_idx]['code_to_value'] = colvm
                    column_metadata[col_idx]['value_to_code'] = dict(zip(values, codes))
                    column_metadata[col_idx]['parameters'] = {'cardinality':  len(values)}
                except:
                    raise utils.BayesDBError('Error parsing vaue map in codebook for {}.'.format(colname))
        else:
            colname_codebook = {
                'description': 'No description',
                'short_name': colname,
                'value_map': None
            }
        column_codebook.append(colname_codebook)

    name_to_idx = dict(zip(colnames, range(num_cols)))
    idx_to_name = dict(zip(map(str, range(num_cols)), colnames))

    M_c = dict(
        name_to_idx=name_to_idx,
        idx_to_name=idx_to_name,
        column_metadata=column_metadata,
        column_codebook=column_codebook
        )
    return M_c


def gen_M_c_from_T_with_colnames(T, colnames):
    num_rows = len(T)
    num_cols = len(T[0])
    #
    gen_numerical_metadata = lambda: dict(modeltype="normal_inverse_gamma",
                                          value_to_code=dict(),
                                          code_to_value=dict())
    column_metadata = [
        gen_numerical_metadata()
        for col_idx in range(num_cols)
        ]
    name_to_idx = dict(zip(colnames, range(num_cols)))
    idx_to_name = dict(zip(map(str, range(num_cols)), colnames))
    M_c = dict(
        name_to_idx=name_to_idx,
        idx_to_name=idx_to_name,
        column_metadata=column_metadata,
        )
    return M_c


def gen_factorial_data_objects(gen_seed, num_clusters, num_cols, num_rows, num_splits, max_mean=10,
                               max_std=1, send_data_inverse_permutation_indices=False):
    T, data_inverse_permutation_indices = gen_factorial_data(gen_seed, num_clusters, num_cols,
                                                             num_rows, num_splits, max_mean,
                                                             max_std)
    T = T.tolist()
    M_r = gen_M_r_from_T(T)
    M_c = gen_M_c_from_T(T)

    if not send_data_inverse_permutation_indices:
        return T, M_r, M_c
    else:
        return T, M_r, M_c, data_inverse_permutation_indices


def discretize_data(T, discretize_indices):
    T_array = numpy.array(T)
    discretize_indices = numpy.array(discretize_indices)
    T_array[:, discretize_indices] = \
        numpy.array(T_array[:, discretize_indices], dtype=int)
    return T_array.tolist()


def convert_columns_to_categorical(T, M_c, categorical_indices):
    categorical_indices = numpy.array(categorical_indices)
    modeltype = 'symmetric_dirichlet_discrete'
    T_array = numpy.array(T)
    for categorical_idx in categorical_indices:
        categorical_column = T_array[:, categorical_idx]
        categorical_column = categorical_column[~numpy.isnan(categorical_column)]
        categorical_values = list(set(categorical_column))
        K = len(categorical_values)
        code_to_value = dict(zip(range(K), categorical_values))
        value_to_code = dict(zip(categorical_values, range(K)))
        categorical_column_metadata = M_c['column_metadata'][categorical_idx]
        categorical_column_metadata['modeltype'] = modeltype
        categorical_column_metadata['code_to_value'] = code_to_value
        categorical_column_metadata['value_to_code'] = value_to_code
    return T, M_c


# UNTESTED
def convert_columns_to_numerical(T, M_c, numerical_indices):
    numerical_indices = numpy.array(numerical_indices)
    modeltype = 'normal_inverse_gamma'
    T_array = numpy.array(T)
    for numerical_idx in numerical_indices:
        code_to_value = dict()
        value_to_code = dict()
        numerical_column_metadata = M_c['column_metadata'][numerical_idx]
        numerical_column_metadata['modeltype'] = modeltype
        numerical_column_metadata['code_to_value'] = code_to_value
        numerical_column_metadata['value_to_code'] = value_to_code
    return T, M_c


def at_most_N_rows(T, N, gen_seed=0):
    num_rows = len(T)
    if (N is not None) and (num_rows > N):
        random_state = numpy.random.RandomState(gen_seed)
        which_rows = random_state.permutation(xrange(num_rows))
        which_rows = which_rows[:N]
        T = [T[which_row] for which_row in which_rows]
    return T


def construct_pandas_df(query_obj):
    """
    Take a result from a BQL statement (dict with 'data' and 'columns')
    and constructs a pandas data frame.

    Currently this is only called if the user specifies pandas_output = True
    """
    if len(query_obj['data']) == 0:
        data = None
    else:
        # Some types (numpy recarray for one) caused some issues when read into
        # a DataFrame, so recasting this as a list of lists solves the problem
        data = [list(row) for row in query_obj['data']]

    # For data queries, we want column_names as the column names in the pandas output.
    # For non-data queries, we only have column_labels, so use that as backup.
    if 'column_names' in query_obj:
        columns = query_obj['column_names']
    else:
        columns = query_obj['column_labels']

    pandas_df = pandas.DataFrame(data=data, columns=columns)
    return pandas_df


def read_pandas_df(pandas_df):
    """
    Takes pandas data frame object and converts data
    into list-of-lists format
    """
    header = list(pandas_df.columns)
    rows = [map(str, row) for index, row in pandas_df.iterrows()]
    return header, rows


def read_csv(filename, has_header=True):
    with open(filename, 'rU') as fh:
        csv_reader = csv.reader(fh)
        header = None
        if has_header:
            header = csv_reader.next()
        rows = [[r.strip() for r in row] for row in csv_reader]
    return header, rows


def write_csv(filename, T, header=None):
    with open(filename, 'w') as fh:
        csv_writer = csv.writer(fh, delimiter=',')
        if header is None:
            csv_writer.writerow(header)
        [csv_writer.writerow(T[i]) for i in range(len(T))]


def all_numerical_from_file(filename, max_rows=None, gen_seed=0, has_header=True):
    header, T = read_csv(filename, has_header=has_header)
    T = numpy.array(T, dtype=float).tolist()
    T = at_most_N_rows(T, N=max_rows, gen_seed=gen_seed)
    M_r = gen_M_r_from_T(T)
    M_c = gen_M_c_from_T(T)
    return T, M_r, M_c, header


def numerical_or_ignore_from_file_with_colnames(filename, cctypes, max_rows=None, gen_seed=0):
    header = None
    T, M_r, M_c = None, None, None
    colmask = map(lambda x: 1 if x != 'ignore' else 0, cctypes)
    with open(filename) as fh:
        csv_reader = csv.reader(fh)
        header = csv_reader.next()
        # TODO: why is this list then an array and then a list again?
        T = numpy.array([[col for col, flag in zip(row, colmask) if flag] for row in csv_reader],
                        dtype=float).tolist()
        num_rows = len(T)
        if (max_rows is not None) and (num_rows > max_rows):
            random_state = numpy.random.RandomState(gen_seed)
            which_rows = random_state.permutation(xrange(num_rows))
            which_rows = which_rows[:max_rows]
            T = [T[which_row] for which_row in which_rows]
        M_r = gen_M_r_from_T(T)
        M_c = gen_M_c_from_T_with_colnames(T, [col for col, flag in zip(header, colmask) if flag])
    return T, M_r, M_c, header


def convert_code_to_value(M_c, cidx, code):
    """
    For a column with categorical data, this function takes the 'code':
    the integer used to represent a specific value, and returns the corresponding
    raw value (e.g. 'Joe' or 234.23409), which is always encoded as a string.

    Note that the underlying store 'value_to_code' is unfortunately named backwards.
    TODO: fix the backwards naming.
    """
    if flexible_isnan(code):
        return code

    column_metadata = M_c['column_metadata'][cidx]
    modeltype = column_metadata['modeltype']
    if modeltype == 'normal_inverse_gamma':
        return float(code)
    elif modeltype == 'vonmises':
        # Convert stored value (in [0, 2pi]) back to raw range.
        param_min = column_metadata['parameters']['min']
        param_max = column_metadata['parameters']['max']
        return param_min + ((float(code) / (2 * pi)) * (param_max - param_min))
    else:
        try:
            return M_c['column_metadata'][cidx]['value_to_code'][int(code)]
        except KeyError:
            return M_c['column_metadata'][cidx]['value_to_code'][str(int(code))]


def convert_value_to_code(M_c, cidx, value):
    """
    For a column with categorical data, this function takes the raw value
    (e.g. 'Joe' or 234.23409), which is always encoded as a string, and returns the
    'code': the integer used to represent that value in the underlying representation.

    Note that the underlying store 'code_to_value' is unfortunately named backwards.
    TODO: fix the backwards naming.
    """
    column_metadata = M_c['column_metadata'][cidx]
    modeltype = column_metadata['modeltype']
    if modeltype == 'normal_inverse_gamma':
        return float(value)
    elif modeltype == 'vonmises':
        param_min = column_metadata['parameters']['min']
        param_max = column_metadata['parameters']['max']
        return (float(value) - param_min) / (param_max - param_min)
    else:
        try:
            return M_c['column_metadata'][cidx]['code_to_value'][str(value)]
        except KeyError:
            raise utils.BayesDBError("Error: value '%s' not in btable." % str(value))


def map_from_T_with_M_c(coordinate_value_tuples, M_c):
    coordinate_code_tuples = []
    column_metadata = M_c['column_metadata']
    for row_idx, col_idx, value in coordinate_value_tuples:
        datatype = column_metadata[col_idx]['modeltype']
        # FIXME: make this robust to different datatypes
        if datatype == 'symmetric_dirichlet_discrete':
            # FIXME: casting key to str is a hack
            value = column_metadata[col_idx]['value_to_code'][str(int(value))]
        coordinate_code_tuples.append((row_idx, col_idx, value))
    return coordinate_code_tuples


def map_to_T_with_M_c(T_uncast_array, M_c):
    T_uncast_array = numpy.array(T_uncast_array)
    # WARNING: array argument is mutated
    for col_idx in range(T_uncast_array.shape[1]):
        column_metadata = M_c['column_metadata'][col_idx]
        modeltype = column_metadata['modeltype']
        col_data = T_uncast_array[:, col_idx]

        if modeltype == 'normal_inverse_gamma':
            continue
        elif modeltype == 'vonmises':
            param_min = column_metadata['parameters']['min']
            param_max = column_metadata['parameters']['max']
            mapped_values = [2 * pi * (float(x) - param_min) / (param_max - param_min)
                             for x in col_data]
        else:
            # copy.copy else you mutate M_c
            mapping = copy.copy(M_c['column_metadata'][col_idx]['code_to_value'])
            mapping['NAN'] = numpy.nan
            to_upper = lambda el: str(el).upper()
            is_nan_str = numpy.array(map(to_upper, col_data)) == 'NAN'
            col_data[is_nan_str] = 'NAN'
            # FIXME: THIS IS WHERE TO PUT NAN HANDLING
            mapped_values = [mapping[el] for el in col_data]
        T_uncast_array[:, col_idx] = mapped_values
    T = numpy.array(T_uncast_array, dtype=float).tolist()
    return T


def do_pop_list_indices(in_list, pop_indices):
    pop_indices = sorted(pop_indices, reverse=True)
    _do_pop = lambda x: in_list.pop(x)
    map(_do_pop, pop_indices)
    return in_list


def get_list_indices(in_list, get_indices_of):
    lookup = dict(zip(in_list, range(len(in_list))))
    indices = map(lookup.get, get_indices_of)
    # The line below removes [0] from indices. Need to check with Jay about how to handle those
    # cases.
    # indices = filter(None, indices)
    return indices


def transpose_list(in_list):
    return zip(*in_list)


def get_pop_indices(cctypes, colnames):
    assert len(colnames) == len(cctypes)
    pop_columns = [colname for (cctype, colname) in zip(cctypes, colnames)
                   if (cctype in ['ignore', 'key'])]
    pop_indices = get_list_indices(colnames, pop_columns)
    return pop_indices


def do_pop_columns(T, pop_indices):
    T_by_columns = transpose_list(T)
    T_by_columns = do_pop_list_indices(T_by_columns, pop_indices)
    T = transpose_list(T_by_columns)
    return T


def remove_ignore_cols(T, cctypes, colnames, parameters=None):
    pop_indices = get_pop_indices(cctypes, colnames)
    T = do_pop_columns(T, pop_indices)
    colnames = do_pop_list_indices(colnames[:], pop_indices)
    cctypes = do_pop_list_indices(cctypes[:], pop_indices)
    if parameters:
        parameters = do_pop_list_indices(parameters[:], pop_indices)
        ret = T, cctypes, colnames, parameters
    else:
        ret = T, cctypes, colnames
    return ret

nan_set = set(['', 'null', 'n/a'])
_convert_nan = lambda el: el if str(el).strip().lower() not in nan_set else 'NAN'
_convert_nans = lambda in_list: map(_convert_nan, in_list)
convert_nans = lambda in_T: map(_convert_nans, in_T)


def flexible_isnan(val):
    try:
        if val in nan_set or numpy.isnan(float(val)):
            return True
    except:
        pass
    return False


def read_data_objects(filename, max_rows=None, gen_seed=0,
                      cctypes=None, colnames=None):
    header, raw_T = read_csv(filename, has_header=True)
    header = [h.lower().strip() for h in header]
    # FIXME: why both accept colnames argument and read header?
    if colnames is None:
        colnames = header
        pass
    # remove excess rows
    raw_T = at_most_N_rows(raw_T, N=max_rows, gen_seed=gen_seed)
    raw_T = convert_nans(raw_T)

    if cctypes is None:
        cctypes = ['numerical'] * len(header)
        pass

    # remove ignore columns
    T_uncast_arr, cctypes, header = remove_ignore_cols(raw_T, cctypes, header)
    # determine value mappings and map T to numerical castable values
    M_r = gen_M_r_from_T(T_uncast_arr)
    M_c = gen_M_c_from_T(T_uncast_arr, cctypes, colnames)
    T = map_to_T_with_M_c(T_uncast_arr, M_c)
    #
    return T, M_r, M_c, header


def get_can_cast_to_float(column_data):
    can_cast = True
    try:
        [float(datum) for datum in column_data]
    except:
        can_cast = False
    return can_cast


def get_can_cast_to_int(column_data):
    can_cast = True
    try:
        [int(datum) for datum in column_data]
    except:
        can_cast = False
    return can_cast


def get_int_equals_str(column_data):
    try:
        equals = all([str(datum) == str(int(datum)) for datum in column_data])
    except:
        equals = False
    return equals


def guess_column_type(column_data, count_cutoff=20):
    num_distinct = len(set(column_data))
    above_count_cutoff = num_distinct > count_cutoff
    can_cast = get_can_cast_to_float(column_data)
    if above_count_cutoff and can_cast:
        column_type = 'numerical'
    else:
        column_type = 'categorical'
    return column_type


def guess_column_types(T, colnames_full, count_cutoff=20, warn_ratio=0.02, warn_cardinality=7):
    """
    Guesses column types - used when creating new btable so user doesn't have to
    specify a type for all columns.
    Refer to function guess_column_type for decision rules.
    Warn if cardinality of a categorical is greater than specified (default 7)
    or if distinctness ratio of numerical is lower than specified (default 0.02).
        (limit proposed by Pat Shafto 7 Aug 2014)
    """
    T_transposed = transpose_list(T)
    column_types = []
    warnings = []
    for column_idx, column_data in enumerate(T_transposed):
        column_type = guess_column_type(column_data, count_cutoff)
        column_types.append(column_type)
        num_data = len(column_data)
        num_distinct = len(set(column_data))
        distinct_ratio = float(num_distinct) / num_data
        if column_type == 'categorical':
            if num_distinct > warn_cardinality:
                warnings.append('Column "%s" is categorical but has a high number of distinct values. '
                            'Convert to numerical using UPDATE SCHEMA if appropriate.'
                            % colnames_full[column_idx])
        elif distinct_ratio < warn_ratio:
            warnings.append('Column "%s" is NOT categorical but has a low percentage of distinct values '
                            '( actual: %0.2f   <   warn threshold: %0.2f ). '
                            'Convert to categorical using UPDATE SCHEMA if appropriate.'
                            % (colnames_full[column_idx], distinct_ratio, warn_ratio))
    return column_types, warnings


def read_model_data_from_csv(filename, max_rows=None, gen_seed=0, cctypes=None):
    colnames, T = read_csv(filename)
    return gen_T_and_metadata(colnames, raw_T, max_rows, gen_seed, cctypes)


def gen_T_and_metadata(colnames, raw_T, max_rows=None, gen_seed=0,
                       cctypes=None, parameters=None, codebook=None):
    T = at_most_N_rows(raw_T, max_rows, gen_seed)
    T = convert_nans(T)
    if cctypes is None:
        cctypes = guess_column_types(T)
    M_c = gen_M_c_from_T(T, cctypes, colnames, parameters, codebook)
    T = map_to_T_with_M_c(numpy.array(T), M_c)
    M_r = gen_M_r_from_T(T)
    return T, M_r, M_c, cctypes

extract_view_count = lambda X_L: len(X_L['view_state'])
extract_cluster_count = lambda view_state_i: view_state_i['row_partition_model']['counts']
extract_cluster_counts = lambda X_L: map(extract_cluster_count, X_L['view_state'])
get_state_shape = lambda X_L: (extract_view_count(X_L), extract_cluster_counts(X_L))


def is_key_eligible(x):
    """
    A column is eligible to be the table key if:
    All values are unique, AND
    can't be cast to float (a string key) OR string representation of all values matches the
    string representation of its int value
    """
    values_unique = len(x) == len(set(x))
    castable = not get_can_cast_to_float(x) or get_int_equals_str(x)
    return values_unique and castable


def select_key_column(raw_T_full, colnames_full, cctypes_full, key_column=None, testing=False):
    """
    This function takes the raw data, colnames, and data types from an input CSV file from
    which a btable is being created.

    It looks for every column that's eligible to be a table key, and prompts the user to select one,
    or create a new key. If no eligible key is found, a new one is created by default.

    That way a btable can't be created without a key column.
    """
    T_df = pandas.DataFrame(data=raw_T_full, columns=colnames_full)
    eligibility = T_df.apply(is_key_eligible)

    key_eligibles = list(eligibility[eligibility].index)
    key_eligibles_len = len(key_eligibles)
    if testing:
        key_column_selection = 0
    elif key_eligibles_len == 0 and key_column is None:
        print("None of the columns in this table is eligible to be the key. A key column will be "
              "created. Press any key continue.")
        user_confirmation = raw_input()
        key_column_selection = 0
    elif key_column is None or key_column not in range(key_eligibles_len + 1):
        key_column_selection = None
        pt = prettytable.PrettyTable()
        pt.field_names = ['choice', 'key column']
        pt.add_row([0, '<Create key column>'])
        for index, key_eligible in enumerate(key_eligibles):
            pt.add_row([index + 1, key_eligible])
        while key_column_selection is None:
            print(str(pt))
            print("Please select which column you would like to set as the table key:")
            user_selection = raw_input()
            try:
                user_selection = int(user_selection)
                if user_selection in range(key_eligibles_len + 1):
                    key_column_selection = user_selection
            except:
                continue
    else:
        key_column_selection = key_column

    # 0 always means insert a new key column.
    if key_column_selection == 0:
        raw_T_full, colnames_full, cctypes_full, key_column = insert_key_column(T_df, colnames_full,
                                                                                cctypes_full)
    else:
        key_column = key_eligibles[key_column_selection - 1]
        cctypes_full[colnames_full.index(key_column)] = 'key'

    return raw_T_full, colnames_full, cctypes_full


def insert_key_column(T_df, colnames_full, cctypes_full):
    """
    Create a new table key column. It'll be the left-most column and an ascending integer column,
    with name 'key' and cctype 'key'.
    """
    key_column_name = 'key'
    if key_column_name in colnames_full:
        key_column_suffix = 0
        while key_column_name + str(key_column_suffix) in colnames_full:
            key_column_suffix += 1
        key_column_name = key_column_name + str(key_column_suffix)
    T_df.insert(0, key_column_name, map(str, range(T_df.shape[0])))
    raw_T_full = T_df.to_records(index=False)
    colnames_full.insert(0, key_column_name)
    cctypes_full.insert(0, 'key')
    return raw_T_full, colnames_full, cctypes_full, key_column_name


def get_column_labels_from_M_c(M_c, colnames):
    """
    Get display labels from M_c by pulling from codebook.
    Sources in order of priority:
        1. column_codebook[col_idx][short_name]
        2. colname
    """

    # Initialize as colnames
    column_labels = colnames[:]

    for colname_idx, colname in enumerate(colnames):
        if colname in M_c['name_to_idx']:
            colname_idx_M_c = M_c['name_to_idx'][colname]
            column_codebook = M_c['column_codebook'][colname_idx_M_c]

            if column_codebook:
                short_name = column_codebook['short_name']
                if short_name != '':
                    column_labels[colname_idx] = short_name

    return column_labels

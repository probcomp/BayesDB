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
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import inspect
import numpy
import os
import re
import inspect
import ast
import pylab
import matplotlib.cm
import time
import pandas
import math
from collections import Counter

import data_utils as du
import select_utils
import functions

class BayesDBError(Exception):
    """ Base class for all other exceptions in this module. """
    pass

class BayesDBParseError(BayesDBError):
    def __init__(self, msg=None):
        if msg:
            self.msg = msg
        else:
            self.msg = "BayesDB parsing error. Try using 'help' to see the help menu for BQL syntax."

    def __str__(self):
        return self.msg

class BayesDBUniqueValueError(BayesDBError):
    def __init__(self, msg=None):
        if msg:
            self.msg = msg
        else:
            self.msg = "BayesDB unique value error. More than one row has this value."

    def __str__(self):
        return self.msg


class BayesDBNoModelsError(BayesDBError):
    def __init__(self, tablename):
        self.tablename = tablename

    def __str__(self):
        return "Btable %s has no models, but this command requires models. Please create models first with INITIALIZE MODELS, and then ANALYZE." % self.tablename

class BayesDBInvalidBtableError(BayesDBError):
    def __init__(self, tablename):
        self.tablename = tablename

    def __str__(self):
        return "Btable %s does not exist. Please create it first with CREATE BTABLE, or view existing btables with LIST BTABLES." % self.tablename

class BayesDBColumnDoesNotExistError(BayesDBError):
    def __init__(self, column, tablename):
        self.column = column
        self.tablename = tablename

    def __str__(self):
        return "Column %s does not exist in btable %s." % (self.column, self.tablename)

class BayesDBColumnListDoesNotExistError(BayesDBError):
    def __init__(self, column_list, tablename):
        self.column_list = column_list
        self.tablename = tablename

    def __str__(self):
        return "Column list %s does not exist in btable %s." % (self.column_list, self.tablename)

class BayesDBRowListDoesNotExistError(BayesDBError):
    def __init__(self, row_list, tablename):
        self.row_list = row_list
        self.tablename = tablename

    def __str__(self):
        return "Row list %s does not exist in btable %s." % (self.row_list, self.tablename)

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def value_string_to_num(value_string):
    if is_int(value_string) == True:
        value = int(value_string)
    elif is_float(value_string) == True:
        value = float(value_string)
    else:
        raise BayesDBParseError("Number expected for value: %s" % value_string)
    return value

def string_to_column_type(value_string, column, M_c):
    """
    column is the string of the column name
    Checks the type of the column in question based on M_c
    If numerical, converts the value from string to int or float
    """
    value = value_string
    if get_cctype_from_M_c(M_c, column) in ['numerical', 'cyclic']:
        if is_int(value_string) == True:
            value = int(value)
        elif is_float(value_string) == True:
            value = float(value)
    return value

def row_id_from_col_value(value, column, M_c, T):
    """
    Returns the row_id of a column where column == value
    If duplicate rows are found, raises exception
    If no rows are found, returns None
    """
    target_row_id = None
    col_idx = M_c['name_to_idx'][column]
    if type(value) == str:
        value = string_to_column_type(value, column, M_c)
    for row_id, T_row in enumerate(T):
        row_values = select_utils.convert_row_from_codes_to_values(T_row, M_c)
        if row_values[col_idx] == value:
            if target_row_id == None:
                target_row_id = row_id
            else:
                raise BayesDBUniqueValueError("Invalid Query: column '%s' has more than one row with value '%s'." %(column, str(value)))
    return target_row_id

##TODO move to engine
def infer(M_c, X_L_list, X_D_list, Y, row_id, col_id, numsamples, confidence, engine):
    q = [row_id, col_id]
    out = engine.call_backend('impute_and_confidence', dict(M_c=M_c, X_L=X_L_list, X_D=X_D_list, Y=Y, Q=[q], n=numsamples))
    code, conf = out
    if conf >= confidence:
      return code
    else:
      return None

def get_imputation_and_confidence_from_samples(M_c, X_L, col_idx, samples):
    samples = numpy.array(samples).T[0]
    modeltype = M_c['column_metadata'][col_idx]['modeltype']
    imputation_function = modeltype_to_imputation_function[modeltype]
    e = imputation_function(samples)
    imputation_confidence_function = modeltype_to_imputation_confidence_function[modeltype]
    column_component_suffstats_i = \
        get_column_component_suffstats_i(M_c, X_L, col_idx)
    imputation_confidence = \
        imputation_confidence_function(samples, e,
                                       column_component_suffstats_i)
    return e, imputation_confidence

    return lambda in_dict: in_dict[name]

def get_column_std(column_component_suffstats_i):
    N = sum(map(lambda in_dict: in_dict['N'], column_component_suffstats_i))
    sum_x = sum(map(lambda in_dict: in_dict['sum_x'], column_component_suffstats_i))
    sum_x_squared = sum(map(lambda in_dict: in_dict['sum_x_squared'], column_component_suffstats_i))
    #
    exp_x = sum_x / float(N)
    exp_x_squared = sum_x_squared / float(N)
    col_var = exp_x_squared - (exp_x ** 2)
    col_std = col_var ** .5
    return col_std


def get_column_component_suffstats_i(M_c, X_L, col_idx):
    column_name = M_c['idx_to_name'][str(col_idx)]
    view_idx = X_L['column_partition']['assignments'][col_idx]
    view_state_i = X_L['view_state'][view_idx]
    local_col_idx = view_state_i['column_names'].index(column_name)
    column_component_suffstats_i = \
        view_state_i['column_component_suffstats'][local_col_idx]
    return column_component_suffstats_i

def numerical_imputation(samples):
    imputed = numpy.median(samples)
    return imputed

def categorical_imputation(samples):
    counter = Counter(samples)
    max_tuple = counter.most_common(1)[0]
    max_count = max_tuple[1]
    counter_counter = Counter(counter.values())
    num_max_count = counter_counter[max_count]
    imputed = max_tuple[0]
    if num_max_count >= 1:
        # if there is a tie, draw randomly
        max_tuples = counter.most_common(num_max_count)
        values = [max_tuple[0] for max_tuple in max_tuples]
        random_state = numpy.random.RandomState()
        draw = random_state.randint(len(values))
        imputed = values[draw]
    return imputed

def categorical_imputation_confidence(samples, imputed, column_hypers_i):
    max_count = sum(numpy.array(samples) == imputed)
    confidence = float(max_count) / len(samples)
    return confidence

def get_numerical_mass_within_delta(samples, center, delta):
    num_samples = len(samples)
    num_within_delta = sum(numpy.abs(samples - center) < delta)
    mass_fraction = float(num_within_delta) / num_samples
    return mass_fraction

def numerical_imputation_confidence(samples, imputed,
                                     column_component_suffstats_i):
    col_std = get_column_std(column_component_suffstats_i)
    delta = .1 * col_std
    confidence = get_numerical_mass_within_delta(samples, imputed, delta)
    return confidence


modeltype_to_imputation_function = {
    'normal_inverse_gamma': numerical_imputation,
    'symmetric_dirichlet_discrete': categorical_imputation,
    }

modeltype_to_imputation_confidence_function = {
    'normal_inverse_gamma': numerical_imputation_confidence,
    'symmetric_dirichlet_discrete': categorical_imputation_confidence,
    }


def check_for_duplicate_columns(column_names):
    column_names_set = set()
    for name in column_names:
        if name in column_names_set:
            raise BayesDBError("Error: Column list has duplicate entries of column: %s" % name)
        column_names_set.add(name)


def get_all_column_names_in_original_order(M_c):
    colname_to_idx_dict = M_c['name_to_idx']
    colnames = map(lambda tup: tup[0], sorted(colname_to_idx_dict.items(), key=lambda tup: tup[1]))
    return colnames

def get_cctype_from_M_c(M_c, column):
    if column in M_c['name_to_idx'].keys():
        column_index = M_c['name_to_idx'][column]
        modeltype = M_c['column_metadata'][column_index]['modeltype']
        if modeltype == 'normal_inverse_gamma':
            cctype = 'numerical'
        elif modeltype == 'vonmises':
            cctype = 'cyclic'
        else:
            cctype = 'categorical'
    else:
        # If the column name wasn't found in metadata, it's a function, so the output will be numerical
        cctype = 'numerical'
    return cctype

# The 'inplace' argument to df.drop() was added to pandas in a version (which one??) that many people may
# not have. So, check to see if 'inplace' exists, otherwise don't pass it -- this just copies the dataframe.
def df_drop(df, column_list, **kwargs):
    if 'inplace' in inspect.getargspec(df.drop).args:
        df.drop(column_list, inplace=True, **kwargs)
    else:
        df = df.drop(column_list, **kwargs)


def summarize_freqs(x, n=5):
    """
    Function to return most frequent n values of each column of the DataFrame being summarized.
    Input: a DataFrame column, by default as Series type
    Input: n, the number of most common values to return (n=5 would be top 5 common values)

    Return: most frequent n values in x.
    """
    x_values, x_freqs, x_probs = get_column_freqs(x)

    if n is not None and len(x_values) > n:
        x_probs = x_probs[:n]
        x_values = x_values[:n]

    # Create index labels ('mode1/2/3/... and prob_mode1/2/3...')
    x_range = range(1, len(x_values) + 1)
    x_index = ['mode' + str(i) if i > 1 else 'mode' for i in x_range]
    x_index += ['prob_mode' + str(i) if i > 1 else 'prob_mode' for i in x_range]

    # Combine values and probabilities into a single list
    x_values.extend(x_probs)

    return pandas.Series(data = x_values, index = x_index)

def freqs(x):
    x_values, x_freqs, x_probs = get_column_freqs(x)
    x_values = pandas.Series(x_values)
    x_probs = pandas.Series(x_probs)
    x_freqs = pandas.Series(x_freqs)

    x_stats = pandas.concat([x_values, x_freqs, x_probs], axis=1)
    return x_stats

def get_column_freqs(x):
    """
    Takes a pandas.Series of data and returns
    1. the unique values
    2. the empirical probabilities of those values
    3. the empirical frequencies of those values
    """
    x_freqs  = x.value_counts()
    x_probs  = list(x_freqs / len(x))
    x_values = list(x_freqs.index)
    x_freqs  = list(x_freqs)

    return x_values, x_freqs, x_probs

def freq_table(data, columns, M_c, remove_key=True):
    """
    Returns a frequency table
    """
    if len(data) > 0:
        # Construct a pandas.DataFrame out of data and columns
        df = pandas.DataFrame(data=data, columns=columns)

        # If the first column is the key (select/infer), summarizing it is meaningless
        if remove_key:
            df_drop(df, [columns[0]], axis=1)

        column = df.columns[0]
        summary_data = freqs(df[column])
        columns = [column, 'frequency', 'probability']
        data = summary_data.to_records(index=False)

    return data, columns

def histogram_table(data, columns, M_c, remove_key=True):
    """
    Returns a frequency table
    """
    if len(data) > 0:
        # Construct a pandas.DataFrame out of data and columns
        df = pandas.DataFrame(data=data, columns=columns)

        # If the first column is the key (select/infer), summarizing it is meaningless
        if remove_key:
            df_drop(df, [columns[0]], axis=1)

        column = df.columns[0]
        
        # numpy.histogram can't deal with NaNs, so block those out
        col_data_no_nans = df[column].dropna()

        if get_cctype_from_M_c(M_c, column) in ['numerical', 'cyclic']:
            # Use Sturges formula to calculate the number of bins to use.
            n_bins = math.ceil(math.log(len(col_data_no_nans), 2) + 1)

            hist_data = numpy.histogram(col_data_no_nans, bins = n_bins)
            bin_mins = hist_data[1][:-1]
            bin_maxs = hist_data[1][1:]
            bin_freqs = hist_data[0]
            bin_probs = bin_freqs / float(sum(bin_freqs))
        else:
            hist_data = col_data_no_nans.value_counts().sort_index()
            bin_mins = list(hist_data.index.values)
            bin_maxs = list(hist_data.index.values)
            bin_freqs = list(hist_data)
            bin_probs = [ float(i)/sum(bin_freqs) for i in bin_freqs ]
            

        summary_data = pandas.DataFrame({
            'bin_minimum': bin_mins,
            'bin_maximum': bin_maxs,
            'frequency'  : bin_freqs,
            'probability': bin_probs
        })

        # Have to reorder columns, otherwise pandas defaults to alphabetical order
        columns = ['bin_minimum', 'bin_maximum', 'frequency', 'probability']
        summary_data = summary_data[columns]
        data = summary_data.to_records(index=False)

    return data, columns

def get_index_from_colname(M_c, column):
    if column in M_c['name_to_idx'].keys():
        return M_c['name_to_idx'][column]

def generate_pairwise_matrix(col_function_name, X_L_list, X_D_list, M_c, T, tablename='', confidence=None, limit=None, engine=None, column_names=None, component_threshold=None):
    """ Compute a matrix. If using a function that requires engine (currently only
    mutual information), engine must not be None. """

    # Get appropriate function
    assert len(X_L_list) == len(X_D_list)
    if col_function_name == 'mutual information':
      if len(X_L_list) == 0:
        return {'message': 'You must initialize models before computing mutual information.'}
      col_function = functions._mutual_information
    elif col_function_name == 'dependence probability':
      if len(X_L_list) == 0:
        return {'message': 'You must initialize models before computing dependence probability.'}
      col_function = functions._dependence_probability
    elif col_function_name == 'correlation':
      col_function = functions._correlation
    else:
      raise BayesDBParseError('Invalid column function: %s' % col_function_name)

    # If using a subset of the columns, get the appropriate names, and figure out their indices.
    if column_names is not None:
        num_cols = len(column_names)
        column_indices = [M_c['name_to_idx'][name] for name in column_names]
    else:
        BayesDBParseError("Invalid query: column '%s' not found" % column)

def summarize_table(data, columns, M_c, remove_key=True):
    """
    Returns a summary of the data.
    Input: data is a list of lists, of raw data values about to be shown to the user.
    Input: columns is a list of column names, as they will be displayed to the user. Note
    that some column names may be things like "row_id" or predictive functions, not actually
    columns.

    Return: columns should be the same, except with another column prepended called like "summaries" or something.
    Return: data should be summaries now.
    """
    if len(data) > 0:
        # Construct a pandas.DataFrame out of data and columns
        df = pandas.DataFrame(data=data, columns=columns)

        # If the first column is the key (select/infer), summarizing it is meaningless
        if remove_key:
            df_drop(df, [columns[0]], axis=1)

        # Get column types as one-row DataFrame
        cctypes = pandas.DataFrame([[get_cctype_from_M_c(M_c, col) for col in df.columns]], columns=df.columns, index=['type'])

        # Run pandas.DataFrame.describe() on each column - it'll compute every stat that it can for each column,
        # depending on its type (assume it's not a problem to overcompute here - for example, computing a mean on a
        # discrete variable with numeric values might not have meaning, but it's easier just to do it and
        # leave interpretation to the user, rather than try to figure out what's meaningful, especially with
        # columns that are the result of predictive functions.
        summary_describe = df.apply(pandas.Series.describe)

        # If there were discrete columns, remove 'top' and 'freq' rows, because we'll replace those
        # with the mode and empirical probabilities
        if 'top' in summary_describe.index and 'freq' in summary_describe.index:
            summary_describe = summary_describe.drop(['top', 'freq'])

        # Past versions used n=5 for 5 most frequent values, but now we have FREQ SELECT for freq tables.
        summary_freqs = df.apply(summarize_freqs, n=1)

        # Attach numerical and discrete summaries along row axis (unaligned values will be assigned NaN)
        summary_data = pandas.concat([cctypes, summary_describe, summary_freqs], axis=0)

        # Reorder rows: count, unique, mean, std, min, 25%, 50%, 75%, max, modes, prob_modes
        if hasattr(summary_data, 'loc'):
            potential_index = pandas.Index(['type', 'count', 'unique', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', \
                'mode', 'mode2', 'mode3', 'mode4', 'mode5', \
                'prob_mode', 'prob_mode2', 'prob_mode3', 'prob_mode4', 'prob_mode5'])

            reorder_index = potential_index[potential_index.isin(summary_data.index)]
            summary_data = summary_data.loc[reorder_index]

        # Insert column of stat descriptions - we're going to leave this column name as a blank to avoid
        # having to prevent column name duplication (allow_duplicates is a newer pandas argument, and can't be sure it's available)
        summary_data.insert(0, '', summary_data.index)

        data = summary_data.to_records(index=False)
        columns = list(summary_data.columns)

    return data, columns

def process_column_list(mixed_list, M_c, column_lists, dedupe=False):
    output = []
    for identifier in mixed_list:
        if identifier == '*':
            output += get_all_column_names_in_original_order(M_c)
        elif column_lists != None and identifier in column_lists.keys():
            output += column_lists[identifier]
        else:
            output.append(identifier)
    if dedupe == True:
        check_for_duplicate_columns(output)
    return output

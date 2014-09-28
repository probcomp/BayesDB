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

import re
import utils
import numpy
import os
import pylab
import matplotlib.cm
import inspect
import operator
import ast
import math
from scipy.stats import pearsonr, chi2_contingency, f_oneway

import utils
import select_utils
import data_utils as du

###
# Three types of function signatures, for each purpose.
#
# SELECT/ORDER BY/WHERE:
# f(args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine)
#
# ESTIMATE COLUMNS
#
#
# First argument of each of these functions is the function-specific argument list,
# which is parsed from parse_<function_name>(), also in this file.
#
# TODO: data_values unused
##

###################################################################
# NORMAL FUNCTIONS (have a separate output value for each row: can ORDER BY, SELECT, etc.)
###################################################################


def _column(column_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    col_idx = column_args[0]
    confidence = column_args[1]
    if confidence is None or not numpy.isnan(T[row_id][col_idx]):
        return du.convert_code_to_value(M_c, col_idx, T[row_id][col_idx])
    else:
        ## Do impute.
        Y = [(row_id, cidx, T[row_id][cidx]) for cidx in M_c['name_to_idx'].values() \
                   if not numpy.isnan(T[row_id][cidx])]
        code = utils.infer(M_c, X_L_list, X_D_list, Y, row_id, col_idx, numsamples,
                           confidence, engine)
        if code is not None:
            # Inferred successfully! Fill in the new value.
            value = du.convert_code_to_value(M_c, col_idx, code)
            return value
        else:
            return du.convert_code_to_value(M_c, col_idx, T[row_id][col_idx])

def _column_ignore(col_idx, row_id, data_values, M_c_full, T_full, engine):
    """
    This function handles selecting data from ignore columns. It's split into a different
    function because it needs to be passed M_c_full and T_full instead of M_c and T, as in _column.
    Since selecting ignore columns is probably a rare event, we can avoid passing M_c_full and T_full
    to _column as "just in case" arguments.
    """
    return du.convert_code_to_value(M_c_full, col_idx, T_full[row_id][col_idx])    

def _row_id(args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    return row_id

def _similarity(similarity_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    target_row_id, target_columns = similarity_args
    return engine.call_backend('similarity', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, given_row_id=row_id, target_row_id=target_row_id, target_columns=target_columns))

def _row_typicality(row_typicality_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    return engine.call_backend('row_structural_typicality', dict(X_L_list=X_L_list, X_D_list=X_D_list, row_id=row_id))

def _predictive_probability(predictive_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    c_idx = predictive_probability_args
    assert type(c_idx) == int    
    Q = [(row_id, c_idx, T[row_id][c_idx])]
    Y = []
    p = math.exp(engine.call_backend('simple_predictive_probability_multistate', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, Y=Y, Q=Q)))
    return p

#####################################################################
# AGGREGATE FUNCTIONS (have only one output value)
#####################################################################
    
def _col_typicality(col_typicality_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    c_idx = col_typicality_args
    assert type(c_idx) == int
    return engine.call_backend('column_structural_typicality', dict(X_L_list=X_L_list, col_id=c_idx))

def _probability(probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    c_idx, value = probability_args
    assert type(c_idx) == int
    try:
        observed = du.convert_value_to_code(M_c, c_idx, value)
    except KeyError:
        # value doesn't exist
        return 0
    row_id = len(X_D_list[0][0]) + 1 ## row is set to 1 + max row, instead of this row.
    Q = [(row_id, c_idx, observed)]
    Y = []
    p = math.exp(engine.call_backend('simple_predictive_probability_multistate', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, Y=Y, Q=Q)))
    return p
    

#########################################################################
## TWO COLUMN AGGREGATE FUNCTIONS (have only one output value, and take two columns as input)
#########################################################################

def _dependence_probability(dependence_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    """
    TODO: THIS NEEDS TO BE A FUNCTION ON CROSSCAT ENGINE! MOVE IT THERE!
    """
    col1, col2 = dependence_probability_args
    prob_dep = 0
    for X_L, X_D in zip(X_L_list, X_D_list):
        assignments = X_L['column_partition']['assignments']
        ## Columns dependent if in same view, and the view has greater than 1 category
        ## Future work can investigate whether more advanced probability of dependence measures
        ## that attempt to take into account the number of outliers do better.
        if (assignments[col1] == assignments[col2]):
            if len(numpy.unique(X_D[assignments[col1]])) > 1 or col1 == col2:
                prob_dep += 1
    prob_dep /= float(len(X_L_list))
    return prob_dep

def _old_dependence_probability(dependence_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    col1, col2 = dependence_probability_args
    prob_dep = 0
    for X_L, X_D in zip(X_L_list, X_D_list):
        assignments = X_L['column_partition']['assignments']
        ## Columns dependent if in same view, and the view has greater than 1 category
        ## Future work can investigate whether more advanced probability of dependence measures
        ## that attempt to take into account the number of outliers do better.
        if (assignments[col1] == assignments[col2]):
            prob_dep += 1
    prob_dep /= float(len(X_L_list))
    return prob_dep

    
def _mutual_information(mutual_information_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    col1, col2 = mutual_information_args
    Q = [(col1, col2)]
    ## Returns list of lists.
    ## First list: same length as Q, so we just take first.
    ## Second list: MI, linfoot. we take MI.
    if numsamples is None:
        numsamples = 100
    # backend n_samples argument specifies samples per model
    n_samples = int(math.ceil(float(numsamples)/len(X_L_list)))
    results_by_model = engine.call_backend('mutual_information', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, Q=Q, n_samples=n_samples))[0][0]
    
    ## Report the average mutual information over each model.
    mi = float(sum(results_by_model)) / len(results_by_model)
    return mi
    
def _correlation(correlation_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    col1, col2 = correlation_args

    # Create map of modeltype to column type. Treate cyclic as numerical for the purpose of calculating correlation.
    cctype_map = dict(normal_inverse_gamma = 'numerical', symmetric_dirichlet_discrete = 'categorical', vonmises = 'numerical')
    cctype1 = cctype_map[M_c['column_metadata'][col1]['modeltype']]
    cctype2 = cctype_map[M_c['column_metadata'][col2]['modeltype']]

    correlation = numpy.nan
    t_array = numpy.array(T, dtype=float)
    nan_index = numpy.logical_or(numpy.isnan(t_array[:,col1]), numpy.isnan(t_array[:,col2]))
    t_array = t_array[numpy.logical_not(nan_index),:]
    n = t_array.shape[0]

    if cctype1 == 'numerical' and cctype2 == 'numerical':
        # Two numerical columns: Pearson R squared
        correlation, p_value = pearsonr(t_array[:,col1], t_array[:,col2])
        correlation = correlation ** 2
    elif cctype1 == 'categorical' and cctype2 == 'categorical':
        # Two categorical columns: Cramer's phi
        data_i = numpy.array(t_array[:, col1], dtype='int32')
        data_j = numpy.array(t_array[:, col2], dtype='int32')
        unique_i = numpy.unique(data_i)
        unique_j = numpy.unique(data_j)
        min_levels = min(len(unique_i), len(unique_j))

        if min_levels >= 2:
            # Create contingency table - built-in way to do this?
            contingency_table = numpy.zeros((len(unique_i), len(unique_j)), dtype='int')
            for i in unique_i:
                for j in unique_j:
                    contingency_table[i][j] = numpy.logical_and(data_i == i, data_j == j).sum()

            chisq, p, dof, expected = chi2_contingency(contingency_table, correction=False)
            correlation = (chisq / (n * (min_levels - 1))) ** 0.5
    else:
        # One numerical, one categorical column: ANOVA R-squared
        if cctype1 == 'categorical':
            data_group = t_array[:, col1]
            data_y = t_array[:, col2]
        else:
            data_group = t_array[:, col2]
            data_y = t_array[:, col1]
        group_values = numpy.unique(data_group)
        n_groups = float(len(group_values))

        if n > n_groups:
            # Use scipy.stats.f_oneway to calculate F-statistic and p-value.
            F, p = f_oneway(*[data_y[data_group == j] for j in group_values])
            # Convert F-stat and number of groups into R-squared.
            correlation = 1 - (1 + F * ((n_groups - 1) / (n - n_groups))) ** -1

    return correlation

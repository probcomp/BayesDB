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
from scipy.stats import pearsonr

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
##

###################################################################
# NORMAL FUNCTIONS (have a separate output value for each row: can ORDER BY, SELECT, etc.)
###################################################################


def _column(column_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, numsamples):
    col_idx = column_args[0]
    confidence = column_args[1] ##TODO Jay, implement this
    return data_values[col_idx]

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
    t_array = numpy.array(T, dtype=float)
    nan_index = numpy.logical_or(numpy.isnan(t_array[:,col1]), numpy.isnan(t_array[:,col2]))
    t_array = t_array[numpy.logical_not(nan_index),:]
    correlation, p_value = pearsonr(t_array[:,col1], t_array[:,col2])
    return correlation

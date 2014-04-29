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


def _column(column_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
    col_idx = column_args
    return data_values[col_idx]

def _row_id(args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
    return row_id

def _similarity(similarity_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
    target_row_id, target_columns = similarity_args
    return engine.call_backend('similarity', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, given_row_id=row_id, target_row_id=target_row_id, target_columns=target_columns))

def _row_typicality(row_typicality_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
    return engine.call_backend('row_structural_typicality', dict(X_L_list=X_L_list, X_D_list=X_D_list, row_id=row_id))

def _predictive_probability(predictive_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
    c_idx = predictive_probability_args
    assert type(c_idx) == int    
    Q = [(row_id, c_idx, T[row_id][c_idx])]
    Y = []
    p = math.exp(engine.call_backend('simple_predictive_probability_multistate', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, Y=Y, Q=Q)))
    return p

#####################################################################
# AGGREGATE FUNCTIONS (have only one output value)
#####################################################################
    
def _col_typicality(col_typicality_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
    c_idx = col_typicality_args
    assert type(c_idx) == int
    return engine.call_backend('column_structural_typicality', dict(X_L_list=X_L_list, col_id=c_idx))

def _probability(probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
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

def _dependence_probability(dependence_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
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

def _old_dependence_probability(dependence_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
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

    
def _mutual_information(mutual_information_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine, n_samples=None):
    col1, col2 = mutual_information_args
    Q = [(col1, col2)]
    ## Returns list of lists.
    ## First list: same length as Q, so we just take first.
    ## Second list: MI, linfoot. we take MI.
    if n_samples is None:
        results_by_model = engine.call_backend('mutual_information', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, Q=Q))[0][0]
    else:
        results_by_model = engine.call_backend('mutual_information', dict(M_c=M_c, X_L_list=X_L_list, X_D_list=X_D_list, Q=Q, n_samples=n_samples))[0][0]                                               
    ## Report the average mutual information over each model.
    mi = float(sum(results_by_model)) / len(results_by_model)
    return mi
    
def _correlation(correlation_args, row_id, data_values, M_c, X_L_list, X_D_list, T, engine):
    col1, col2 = correlation_args
    t_array = numpy.array(T, dtype=float)
    nan_index = numpy.logical_or(numpy.isnan(t_array[:,col1]), numpy.isnan(t_array[:,col2]))
    t_array = t_array[numpy.logical_not(nan_index),:]
    correlation, p_value = pearsonr(t_array[:,col1], t_array[:,col2])
    return correlation


##############################################
# function parsing
##############################################

def parse_predictive_probability(function_group, M_c):
    """
    Returns a tuple of function, column_index, aggregate
    """
    if function_group.column != '' and function_group.column in M_c['name_to_idx']:
        column = function_group.column
    elif function_group.column != '':
        raise utils.BayesDBParseError("Invalid query: could not parse '%s'" % function_group.column)
    else:
        raise utils.BayesDBParseError("Invalid query: missing column argument")
    return (_predictive_probability, column, False)

def parse_probability(function_group, M_c):
    column = function_group.column
    c_idx = M_c['name_to_idx'][column]
    value = utils.string_to_value(function_group.value)
    return (_probability, (c_idx, value), True)

def parse_similarity(function_group, M_c, T, column_lists):
    row_clause = function_group.row_clause
    target_row_id = None
    ## Case where given row_id
    if row_clause.row_id != '':
        target_row_id = int(row_id)
    ## Row id is of the form: column = value where value is unique
    elif row_clause.column != '':
        target_col_name = row_clause.column
        target_col_value = utils.string_to_value(row_clause.column_value)
        target_col_idx = M_c['name_to_idx'][target_col_name]
        for row_id, T_row in enumerate(T):
          row_values = select_utils.convert_row_from_codes_to_values(T_row, M_c)
          if row_values[target_col_idx] == target_col_value:
            target_row_id = row_id
            break
    with_respect_to_clause = function_group.with_respect_to
    if with_respect_to_clause != '':
        column_set = with_respect_to_clause.column_list
        target_column_names = []
        for column_name in column_set:
            if column_name == '*':
                target_columns = None
                break
            elif column_lists is not None and column_name in column_lists.keys():
                target_column_names.append(column_lists[column_name])
            elif column_name in M_c['name_to_idx']:
                target_column_names.append(column_name)
            else:
                raise utils.BayesDBParseError("Invalid query: column '%s' not found" % column_name)
        target_columns = [M_c['name_to_idx'][column_name] for column_name in target_column_names]
    
    return target_row_id, target_columns

def aparse_similarity(colname, M_c, T, column_lists):
  """
  colname: this is the thing that we want to try to parse as a similarity.
  It is an entry in a query's columnstring. eg: SELECT colname1, colname2 FROM...
  We are checking if colname matches "SIMILARITY TO <rowid> [WITH RESPECT TO <col>]"
  it is NOT just the column name
  """
  similarity_match = re.search(r"""
      similarity\s+to\s+
      (\()?
      (?P<rowid>[^,\)\(]+)
      (\))?
      \s+with\s+respect\s+to\s+
      (?P<columnstring>.*$)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if not similarity_match:
    similarity_match = re.search(r"""
      similarity\s+to\s+
      (\()?
      (?P<rowid>[^,\)\(]+)
      (\))?
      \s*$
    """, colname, re.VERBOSE | re.IGNORECASE)
  if similarity_match:
      rowid = similarity_match.group('rowid').strip()
      if utils.is_int(rowid):
        target_row_id = int(rowid)
      else:
        ## Instead of specifying an integer for rowid, you can specify a simple where clause.
        where_vals = rowid.split('=')
        where_colname = where_vals[0]
        where_val = where_vals[1]
        if type(where_val) == str or type(where_val) == unicode:
          where_val = ast.literal_eval(where_val)
        ## Look up the row_id where this column has this value!
        c_idx = M_c['name_to_idx'][where_colname.lower()]
        for row_id, T_row in enumerate(T):
          row_values = select_utils.convert_row_from_codes_to_values(T_row, M_c)
          if row_values[c_idx] == where_val:
            target_row_id = row_id
            break

      if 'columnstring' in similarity_match.groupdict() and similarity_match.group('columnstring'):
          columnstring = similarity_match.group('columnstring').strip()

          target_colnames = [colname.strip() for colname in utils.column_string_splitter(columnstring, M_c, column_lists)]
          utils.check_for_duplicate_columns(target_colnames)
          target_columns = [M_c['name_to_idx'][colname] for colname in target_colnames]
      else:
          target_columns = None

      return target_row_id, target_columns
  else:
      return None

## TODO deprecate
def parse_similarity_pairwise(colname, M_c, _, column_lists):
  """
  TODO: this is horribly hacky.
  Note that this function returns False if it doesn't parse; different from normal.
  
  colname: this is the thing that we want to try to parse as a similarity.
  It is an entry in a query's columnstring. eg: SELECT colname1, colname2 FROM...
  We are checking if colname matches "SIMILARITY TO <rowid> [WITH RESPECT TO <col>]"
  it is NOT just the column name
  """
  similarity_match = re.search(r"""
      similarity\s+with\s+respect\s+to\s+
      (?P<columnstring>.*$)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if not similarity_match:
    similarity_match = re.search(r"""
      similarity
    """, colname, re.VERBOSE | re.IGNORECASE)
  if similarity_match:
      if 'columnstring' in similarity_match.groupdict() and similarity_match.group('columnstring'):
          columnstring = similarity_match.group('columnstring').strip()

          target_colnames = [colname.strip() for colname in utils.column_string_splitter(columnstring, M_c, column_lists)]
          utils.check_for_duplicate_columns(target_colnames)
          target_columns = [M_c['name_to_idx'][colname] for colname in target_colnames]
      else:
          target_columns = None

      return target_columns
  else:
      return False
      
def parse_typicality(function_group, M_c):
    '''
    Returns a tuple of typicality_function, args, aggregate
    '''
    if function_group.column == '':
        return _row_typicality, None, False
    else:
        colname = function_group.column
        ##TODO Throw incorrect col_name exception
        return _col_typicality, M_c['name_to_idx'][colname], True


def parse_mutual_information(colname, M_c):
  mutual_information_match = re.search(r"""
      mutual_information
      \s*\(\s*
      (?P<col1>[^\s]+)
      \s*,\s*
      (?P<col2>[^\s]+)
      \s*\)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if not mutual_information_match:
    mutual_information_match = re.search(r"""
      MUTUAL\s+INFORMATION\s+OF\s+
      (?P<col1>[^\s]+)
      \s+(WITH|TO)\s+
      (?P<col2>[^\s]+)
    """, colname, re.VERBOSE | re.IGNORECASE)    
  if mutual_information_match:
      col1 = mutual_information_match.group('col1')
      col2 = mutual_information_match.group('col2')
      col1, col2 = M_c['name_to_idx'][col1.lower()], M_c['name_to_idx'][col2.lower()]
      return col1, col2
  else:
      return None

def parse_dependence_probability(colname, M_c):
  dependence_probability_match = re.search(r"""
    DEPENDENCE\s+PROBABILITY\s+OF\s+
    (?P<col1>[^\s]+)
    \s+(WITH|TO)\s+
    (?P<col2>[^\s]+)
  """, colname, re.VERBOSE | re.IGNORECASE)    
  if dependence_probability_match:
      col1 = dependence_probability_match.group('col1')
      col2 = dependence_probability_match.group('col2')
      col1, col2 = M_c['name_to_idx'][col1.lower()], M_c['name_to_idx'][col2.lower()]
      return col1, col2
  else:
      return None

        
def parse_correlation(colname, M_c):
  correlation_match = re.search(r"""
    CORRELATION\s+OF\s+
    (?P<col1>[^\s]+)
    \s+(WITH|TO)\s+
    (?P<col2>[^\s]+)
  """, colname, re.VERBOSE | re.IGNORECASE)    
  if correlation_match:
      col1 = correlation_match.group('col1')
      col2 = correlation_match.group('col2')
      col1, col2 = M_c['name_to_idx'][col1.lower()], M_c['name_to_idx'][col2.lower()]
      return col1, col2
  else:
      return None

        
#########################
# single-column versions
#########################

## TODO deprecate
def parse_cfun_column_typicality(colname, M_c):
  col_typicality_match = re.search(r"""
      ^\s*
      TYPICALITY
      \s*$
  """, colname, flags=re.VERBOSE | re.IGNORECASE)
  if col_typicality_match:
      return True
  else:
      return None

def parse_cfun_mutual_information(colname, M_c):
  mutual_information_match = re.search(r"""
      MUTUAL\s+INFORMATION\s+
      (WITH|TO)\s+
      ['"]?
      (?P<col1>[^\s'"]+)
      ['"]?
  """, colname, re.VERBOSE | re.IGNORECASE)    
  if mutual_information_match:
      col1 = mutual_information_match.group('col1')
      return M_c['name_to_idx'][col1.lower()]
  else:
      return None

def parse_cfun_dependence_probability(colname, M_c):
  dependence_probability_match = re.search(r"""
    DEPENDENCE\s+PROBABILITY\s+
    (WITH|TO)\s+
    ['"]?
    (?P<col1>[^\s'"]+)
    ['"]?
  """, colname, re.VERBOSE | re.IGNORECASE)
  if dependence_probability_match:
      col1 = dependence_probability_match.group('col1')
      return M_c['name_to_idx'][col1.lower()]
  else:
      return None

def parse_cfun_correlation(colname, M_c):
  correlation_match = re.search(r"""
    CORRELATION\s+
    (WITH|TO)\s+
    ['"]?
    (?P<col1>[^\s'"]+)
    ['"]?
  """, colname, re.VERBOSE | re.IGNORECASE)    
  if correlation_match:
      col1 = correlation_match.group('col1')
      return M_c['name_to_idx'][col1.lower()]
  else:
      return None

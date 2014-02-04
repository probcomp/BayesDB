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
import crosscat.utils.data_utils as du

###
# Three types of function signatures, for each purpose.
#
# SELECT/ORDER BY/WHERE:
# f(args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend)
#
# ESTIMATE COLUMNS
##

###################################################################
# NORMAL FUNCTIONS (have a separate output value for each row: can ORDER BY, SELECT, etc.)
###################################################################
  
def _column(column_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    col_idx = column_args
    return data_values[col_idx]

def _row_id(args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    return row_id

def _similarity(similarity_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    target_row_id, target_column = similarity_args
    return backend.similarity(M_c, X_L_list, X_D_list, row_id, target_row_id, target_column)

def _row_typicality(row_typicality_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    return backend.row_structural_typicality(X_L_list, X_D_list, row_id)

def _predictive_probability(predictive_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    c_idx = predictive_probability_args
    assert type(c_idx) == int    
    ## WARNING: this backend call doesn't work for multinomial
    ## TODO: need to test
    Q = [(row_id, c_idx, T[row_id][c_idx])]
    Y = []
    p = math.exp(backend.simple_predictive_probability_multistate(M_c, X_L_list, X_D_list, Y, Q))    
    return p

def _probability(probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    c_idx, value = probability_args
    assert type(c_idx) == int
    observed = du.convert_value_to_code(M_c, c_idx, value)
    row_id = len(X_D_list[0][0]) + 1 ## row is set to 1 + max row, instead of this row.
    Q = [(row_id, c_idx, observed)]
    Y = []
    p = math.exp(backend.simple_predictive_probability_multistate(M_c, X_L_list, X_D_list, Y, Q))
    return p


#####################################################################
# AGGREGATE FUNCTIONS (have only one output value)
#####################################################################
    
def _col_typicality(col_typicality_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    c_idx = col_typicality_args
    assert type(c_idx) == int
    return backend.column_structural_typicality(X_L_list, c_idx)


#########################################################################
## TWO COLUMN AGGREGATE FUNCTIONS (have only one output value, and take two columns as input)
#########################################################################

def _dependence_probability(dependence_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    col1, col2 = dependence_probability_args
    prob_dep = 0
    for X_L, X_D in zip(X_L_list, X_D_list):
        assignments = X_L['column_partition']['assignments']
        ## Columns dependent if in same view, and the view has greater than 1 category
        ## Future work can investigate whether more advanced probability of dependence measures
        ## that attempt to take into account the number of outliers do better.
        if (assignments[col1] == assignments[col2]):
            if len(numpy.unique(X_D[assignments[col1]])) > 1:
                prob_dep += 1
    prob_dep /= float(len(X_L_list))
    return prob_dep

def _old_dependence_probability(dependence_probability_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
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

    
def _mutual_information(mutual_information_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend, n_samples=None):
    col1, col2 = mutual_information_args
    Q = [(col1, col2)]
    ## Returns list of lists.
    ## First list: same length as Q, so we just take first.
    ## Second list: MI, linfoot. we take MI.
    if n_samples is None:
        results_by_model = backend.mutual_information(M_c, X_L_list, X_D_list, Q)[0][0]
    else:
        results_by_model = backend.mutual_information(M_c, X_L_list, X_D_list, Q, n_samples=n_samples)[0][0]
    ## Report the average mutual information over each model.
    mi = float(sum(results_by_model)) / len(results_by_model)

    ## TODO: is this implementation right, or is the above one?
    #c_idx1, c_idx2 = args
    #mutual_info, linfoot = backend.mutual_information(M_c, X_L_list, X_D_list, [(c_idx1, c_idx2)])
    #mutual_info = numpy.mean(mutual_info)
    
    return mi
    
def _correlation(correlation_args, row_id, data_values, M_c, X_L_list, X_D_list, T, backend):
    col1, col2 = correlation_args
    t_array = numpy.array(T, dtype=float)
    correlation, p_value = pearsonr(t_array[:,col1], t_array[:,col2])
    return correlation




##############################################
# function parsing
##############################################

def parse_predictive_probability(colname, M_c):
  prob_match = re.search(r"""
      PREDICTIVE\s+PROBABILITY\s+OF\s+
      (?P<column>[^\s]+)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if prob_match:
    column = prob_match.group('column')
    c_idx = M_c['name_to_idx'][column]
    return c_idx
  else:
    return None

def parse_probability(colname, M_c):
  prob_match = re.search(r"""
      ^PROBABILITY\s+OF\s+
      (?P<column>[^\s]+)\s*=\s*(\'|\")?\s*(?P<value>[^\'\"]*)\s*(\'|\")?$
    """, colname, re.VERBOSE | re.IGNORECASE)
  if prob_match:
    column = prob_match.group('column')
    c_idx = M_c['name_to_idx'][column]
    value = prob_match.group('value')
    if utils.is_int(value):
      value = int(value)
    elif utils.is_float(value):
      value = float(value)
    ## TODO: need to escape strings here with ast.eval... call?
    return c_idx, value
  else:
    return None

def parse_similarity(colname, M_c, T):
  """
  colname: this is the thing that we want to try to parse as a similarity.
  It is an entry in a query's columnstring. eg: SELECT colname1, colname2 FROM...
  We are checking if colname matches "SIMILARITY TO <rowid> [WITH RESPECT TO <col>]"
  """
  similarity_match = re.search(r"""
      similarity\s+to\s+
      (\()?
      (?P<rowid>[^,\)\(]+)
      (\))?
      \s+with\s+respect\s+to\s+
      (?P<column>[^\s]+)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if not similarity_match:
    similarity_match = re.search(r"""
      similarity\s+to\s+
      (?P<rowid>[^,]+)
    """, colname, re.VERBOSE | re.IGNORECASE)
  ## Try 2nd type of similarity syntax. Add "contextual similarity" for when cols are present?
  if not similarity_match:
    similarity_match = re.search(r"""
        similarity_to\s*\(\s*
        (?P<rowid>[^,]+)
        (\s*,\s*(?P<column>[^\s]+)\s*)?
        \s*\)
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

      if 'column' in similarity_match.groupdict() and similarity_match.group('column'):
          target_column = similarity_match.group('column').strip()
          target_column = M_c['name_to_idx'][target_column]
      else:
          target_column = None

      return target_row_id, target_column
  else:
      return None

def parse_row_typicality(colname):
    row_typicality_match = re.search(r"""
        ^\s*    
        ((row_typicality)|
        (^\s*TYPICALITY\s*$))
        \s*$
    """, colname, re.VERBOSE | re.IGNORECASE)
    if row_typicality_match:
        return True
    else:
        return None

def parse_column_typicality(colname, M_c):
  col_typicality_match = re.search(r"""
      col_typicality
      \s*
      \(\s*
      (?P<column>[^\s]+)
      \s*\)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if not col_typicality_match:
      col_typicality_match = re.search(r"""
      ^\s*
      TYPICALITY\s+OF\s+
      (?P<column>[^\s]+)
      \s*$
      """, colname, flags=re.VERBOSE | re.IGNORECASE)
  if col_typicality_match:
      colname = col_typicality_match.group('column').strip()
      return M_c['name_to_idx'][colname]
  else:
      return None

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
      col1, col2 = M_c['name_to_idx'][col1], M_c['name_to_idx'][col2]
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
      col1, col2 = M_c['name_to_idx'][col1], M_c['name_to_idx'][col2]
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
      col1, col2 = M_c['name_to_idx'][col1], M_c['name_to_idx'][col2]
      return col1, col2
  else:
      return None

        
#########################
# single-column versions
#########################

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
      (?P<col1>[^\s]+)
  """, colname, re.VERBOSE | re.IGNORECASE)    
  if mutual_information_match:
      col1 = mutual_information_match.group('col1')
      return M_c['name_to_idx'][col1]
  else:
      return None

def parse_cfun_dependence_probability(colname, M_c):
  dependence_probability_match = re.search(r"""
    DEPENDENCE\s+PROBABILITY\s+
    (WITH|TO)\s+  
    (?P<col1>[^\s]+)
  """, colname, re.VERBOSE | re.IGNORECASE)    
  if dependence_probability_match:
      col1 = dependence_probability_match.group('col1')
      return M_c['name_to_idx'][col1]      
  else:
      return None

def parse_cfun_correlation(colname, M_c):
  correlation_match = re.search(r"""
    CORRELATION\s+
    (WITH|TO)\s+
    (?P<col1>[^\s]+)
  """, colname, re.VERBOSE | re.IGNORECASE)    
  if correlation_match:
      col1 = correlation_match.group('col1')
      return M_c['name_to_idx'][col1]      
  else:
      return None

#
#   Copyright (c) 2010-2013, MIT Probabilistic Computing Project
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

import numpy
import os
import re
import inspect
import ast
import pylab
import matplotlib.cm
import time
from scipy.stats import pearsonr

import crosscat.utils.data_utils as du
import select_utils

''' Derived quantities
--orderables (function of a row,col):
col
probability(col=val)
similarity to row [wrt <col>]
typicality
predictive probability(same as probability, but with observed value)

--functions of one col ("aggregates"):
centrality
dependence probability to <col>
mutual information with <col>
correlation with <col>

--functions of two cols (for estimate pairwise):
mutual information
dependence probability
correlation


orderable syntax:
_get_x_function(args, X_L_list, X_D_list, M_c, T): returns func of row_id, data_values

one col functions:

two col syntax:
function of col1, col2, X_L_list, X_D_list, M_c, T
'''

########################################################################

def _get_column_function(column, M_c):
  """
  Returns a function of the form required by order_by that returns the column value.
  data_values is one row
  """
  col_idx = M_c['name_to_idx'][column]
  return lambda row_id, data_values: data_values[col_idx]

def _get_similarity_function(target_column, target_row_id, X_L_list, X_D_list, M_c, T, backend):
  """
  Call this function to get a version of similarity as a function of only (row_id, data_values).
  data_values is one row
  """
  if type(target_row_id) == str or type(target_row_id) == unicode:
    ## Instead of specifying an integer for rowid, you can specify a where clause.
    where_vals = target_row_id.split('=')
    where_colname = where_vals[0]
    where_val = where_vals[1]
    if type(where_val) == str:
      where_val = ast.literal_eval(where_val)
    ## Look up the row_id where this column has this value!
    c_idx = M_c['name_to_idx'][where_colname.lower()]
    for row_id, T_row in enumerate(T):
      row_values = select_utils.convert_row(T_row, M_c)
      if row_values[c_idx] == where_val:
        target_row_id = row_id
        break
  return lambda row_id, data_values: backend.similarity(M_c, X_L_list, X_D_list, row_id, target_row_id, target_column)


#########################################################################
## TWO COLUMN FUNCTIONS
########################################################################

def _dependence_probability(col1, col2, X_L_list, X_D_list, M_c, T, backend=None):
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

def _view_similarity(col1, col2, X_L_list, X_D_list, M_c, T, backend=None):
  prob_dep = 0
  for X_L in X_L_list:
    assignments = X_L['column_partition']['assignments']
    if assignments[col1] == assignments[col2]:
      prob_dep += 1
  prob_dep /= float(len(X_L_list))
  return prob_dep

def _mutual_information(col1, col2, X_L_list, X_D_list, M_c, T, backend):
  Q = [(col1, col2)]
  ## Returns list of lists.
  ## First list: same length as Q, so we just take first.
  ## Second list: MI, linfoot. we take MI.
  results_by_model = backend.mutual_information(M_c, X_L_list, X_D_list, Q, n_samples=1)[0][0]
  ## Report the average mutual information over each model.
  mi = float(sum(results_by_model)) / len(results_by_model)
  return mi

def _correlation(col1, col2, X_L_list, X_D_list, M_c, T, backend=None):
  t_array = numpy.array(T, dtype=float)
  correlation, p_value = pearsonr(t_array[:,col1], t_array[:,col2])
  return correlation


########################################################################        

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

def column_string_splitter(columnstring):
    paren_level = 0
    output = []
    current_column = []
    for c in columnstring:
      if c == '(':
        paren_level += 1
      elif c == ')':
        paren_level -= 1

      if c == ',' and paren_level == 0:
          if '*' in current_column:
              for idx in range(len(M_c['name_to_idx'].keys())):
                  output.append(M_c['idx_to_name'][str(idx)])
          else:
              output.append(''.join(current_column))
          current_column = []
      else:
        current_column.append(c)
    output.append(''.join(current_column))
    return output

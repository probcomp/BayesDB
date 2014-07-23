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

import utils
import functions
import data_utils as du


def filter_column_indices(column_indices, where_conditions, M_c, T, X_L_list, X_D_list, engine, numsamples):
  # should return tuples of the form (data, c_idx), where data is a list of the values of each of the where functions.
  column_indices_and_data = []

  for c_idx in column_indices:
    data = []
    
    for ((func, f_args), op, val) in where_conditions:
      # mutual_info, correlation, and dep_prob all take args=(i,j)
      # col_typicality takes just args=i
      # incoming f_args will be None for col_typicality, j for the three others
      if f_args is not None:
        f_args = (f_args, c_idx)
      else:
        f_args = c_idx
      where_value = func(f_args, None, None, M_c, X_L_list, X_D_list, T, engine, numsamples)
      data.append(where_value)
      if not op(where_value, val):
        break
        
    column_indices_and_data.append((data, c_idx))
    
  return column_indices_and_data



  
  return [c_idx for c_idx in column_indices if _is_column_valid(c_idx, where_conditions, M_c, X_L_list, X_D_list, T, engine, numsamples)]

def _is_column_valid(c_idx, where_conditions, M_c, X_L_list, X_D_list, T, engine, numsamples):
  for ((func, f_args), op, val) in where_conditions:
    # mutual_info, correlation, and dep_prob all take args=(i,j)
    # col_typicality takes just args=i
    # incoming f_args will be None for col_typicality, j for the three others
    if f_args is not None:
      f_args = (f_args, c_idx)
    else:
      f_args = c_idx
    where_value = func(f_args, None, None, M_c, X_L_list, X_D_list, T, engine, numsamples)
    return op(where_value, val)
  return True


def order_columns(column_indices, order_by, M_c, X_L_list, X_D_list, T, engine, numsamples):
  if not order_by:
    return column_indices
  return _column_order_by(column_indices, order_by, M_c, X_L_list, X_D_list, T, engine, numsamples)


def _column_order_by(column_indices_and_data, function_list, M_c, X_L_list, X_D_list, T, engine, numsamples):
  """
  Return the original column indices, but sorted by the individual functions.
  """
  if len(column_indices_and_data) == 0 or not function_list:
    return column_indices_and_data

  scored_column_indices = list() ## Entries are (score, cidx, data)
  for data, c_idx in column_indices_and_data:
    ## Apply each function to each cidx to get a #functions-length tuple of scores.
    scores = []
    values = []
    for (f, f_args, desc) in function_list:

      # mutual_info, correlation, and dep_prob all take args=(i,j)
      # col_typicality takes just args=i
      # incoming f_args will be None for col_typicality, j for the three others
      if f_args:
        f_args = (f_args, c_idx)
      else:
        f_args = c_idx

      score = f(f_args, None, None, M_c, X_L_list, X_D_list, T, engine, numsamples)
      data.append(score)
      # nan values create really unpredictable sort behavior, so set score to inf for consistency
      if numpy.isnan(score):
        score = float('inf')
      elif desc:
        score *= -1
      scores.append(score)
    scored_column_indices.append((tuple(scores), c_idx, tuple(data)))
  scored_column_indices.sort(key=lambda tup: tup[0], reverse=False)

  return [(data, c_idx) for (scores, c_idx, data) in scored_column_indices]

def function_description(func, f_args, M_c):
  function_names = {'_col_typicality': 'typicality',
    '_dependence_probability': 'dependence probability',
    '_correlation': 'correlation',
    '_mutual_information': 'mutual information'
    }

  function_name = function_names[func.__name__]

  if function_name == 'typicality':
    description = 'typicality'
  elif f_args is not None:
    function_arg = M_c['idx_to_name'][str(f_args)]
    description = '%s with %s' % (function_name, function_arg)
  else:
    raise utils.BayesDBError()

  return description


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
import crosscat.utils.data_utils as du

def filter_column_indices(column_indices, where_conditions, M_c, T, X_L_list, X_D_list, backend):
  return [c_idx for c_idx in column_indices if _is_column_valid(c_idx, where_conditions, M_c, X_L_list, X_D_list, T, backend)]

def _is_column_valid(c_idx, where_conditions, M_c, X_L_list, X_D_list, T, backend):
    for ((func, f_args), op, val) in where_conditions:
        # mutual_info, correlation, and dep_prob all take args=(i,j)
        # col_typicality takes just args=i
        # incoming f_args will be None for col_typicality, j for the three others
        if f_args:
            f_args = (f_args, c_idx)
        else:
            f_args = c_idx
      
        where_value = func(f_args, None, None, M_c, X_L_list, X_D_list, T, backend)
        return op(where_value, val)
    return True

def get_conditions_from_column_whereclause(whereclause, M_c, T):
  ## Create conds: the list of conditions in the whereclause.
  ## List of (c_idx, op, val) tuples.
  conds = list() 
  if len(whereclause) > 0:
    conditions = re.split(r'and', whereclause, flags=re.IGNORECASE)
    ## Order matters: need <= and >= before < and > and =.
    operator_list = ['<=', '>=', '=', '>', '<']
    operator_map = {'<=': operator.le, '<': operator.lt, '=': operator.eq, '>': operator.gt, '>=': operator.ge}

    # TODO: parse this properly with pyparsing
    # note that there can be more than one operator!
    # if 1 total: we want that one. if 2 total: we want 2nd (assuming probably query on left). if 3 total: we want 2nd.
    
    for condition in conditions:
      for operator_str in operator_list:
        if operator_str in condition:
          op_str = operator_str
          op = operator_map[op_str]
          break
      vals = condition.split(op_str)
      raw_string = vals[0].strip()

      ## Determine what type the value is
      raw_val = vals[1].strip()
      if utils.is_int(raw_val):
        val = int(raw_val)
      elif utils.is_float(raw_val):
        val = float(raw_val)
      else:
        ## val could have matching single or double quotes, which we can safely eliminate
        ## with the following safe (string literal only) implementation of eval
        val = ast.literal_eval(raw_val).lower()


      t = functions.parse_cfun_column_typicality(raw_string, M_c)
      if t:
        conds.append(((functions._col_typicality, None), op, val))
        continue

      d = functions.parse_cfun_dependence_probability(raw_string, M_c)
      if d:
        conds.append(((functions._dependence_probability, d), op, val))
        continue

      m = functions.parse_cfun_mutual_information(raw_string, M_c)
      if m is not None:
        conds.append(((functions._mutual_information, m), op, val))
        continue

      c= functions.parse_cfun_correlation(raw_string, M_c)
      if c is not None:
        conds.append(((functions._correlation, c), op, val))
        continue

      raise Exception("Invalid query argument: could not parse '%s'" % raw_string)    
  return conds
    

def order_columns(column_indices, order_by, M_c, X_L_list, X_D_list, T, backend):
  if not order_by:
    return column_indices
  # Step 1: get appropriate functions.
  function_list = list()
  for orderable in order_by:
    assert type(orderable) == tuple and type(orderable[0]) == str and type(orderable[1]) == bool
    raw_orderable_string = orderable[0]
    desc = orderable[1]

    ## function_list is a list of
    ##   (f(args, row_id, data_values, M_c, X_L_list, X_D_list, backend), args, desc)

    t = functions.parse_cfun_column_typicality(raw_orderable_string, M_c)
    if t:
      function_list.append((functions._col_typicality, None, desc))
      continue

    d = functions.parse_cfun_dependence_probability(raw_orderable_string, M_c)
    if d:
      function_list.append((functions._dependence_probability, d, desc))
      continue

    m = functions.parse_cfun_mutual_information(raw_orderable_string, M_c)
    if m is not None:
      function_list.append((functions._mutual_information, m, desc))
      continue

    c= functions.parse_cfun_correlation(raw_orderable_string, M_c)
    if c is not None:
      function_list.append((functions._correlation, c, desc))
      continue

    raise Exception("Invalid query argument: could not parse '%s'" % raw_orderable_string)    

  ## Step 2: call order by.
  sorted_column_indices = _column_order_by(column_indices, function_list, M_c, X_L_list, X_D_list, T, backend)
  return sorted_column_indices

def _column_order_by(column_indices, function_list, M_c, X_L_list, X_D_list, T, backend):
  """
  Return the original column indices, but sorted by the individual functions.
  """
  if len(column_indices) == 0 or not function_list:
    return column_indices

  scored_column_indices = list() ## Entries are (score, cidx)
  for c_idx in column_indices:
    ## Apply each function to each cidx to get a #functions-length tuple of scores.
    scores = []
    for (f, f_args, desc) in function_list:

      # mutual_info, correlation, and dep_prob all take args=(i,j)
      # col_typicality takes just args=i
      # incoming f_args will be None for col_typicality, j for the three others
      if f_args:
        f_args = (f_args, c_idx)
      else:
        f_args = c_idx
        
      score = f(f_args, None, None, M_c, X_L_list, X_D_list, T, backend)
      if desc:
        score *= -1
      scores.append(score)
    scored_column_indices.append((tuple(scores), c_idx))
  scored_column_indices.sort(key=lambda tup: tup[0], reverse=False)

  return [tup[1] for tup in scored_column_indices]

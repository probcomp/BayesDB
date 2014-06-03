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
import string

import utils
import functions
import data_utils as du
from pyparsing import *
import bayesdb.bql_grammar as bql_grammar

def is_row_valid(idx, row, where_conditions, M_c, X_L_list, X_D_list, T, backend, tablename, numsamples):
  """Helper function that applies WHERE conditions to row, returning True if row satisfies where clause."""
  ## TODO make better, this takes no where conditions to mean that all rows are valid
  if where_conditions == None:
    return True
  for ((func, f_args), op, val) in where_conditions:
    where_value = func(f_args, idx, row, M_c, X_L_list, X_D_list, T, backend, numsamples)    
    if func != functions._row_id:
      if not op(where_value, val):
        return False
    else:
      ## val should be a row list name in this case. look up the row list, and set val to be the list of row indices
      ## in the row list. Throws BayesDBRowListDoesNotExistError if row list does not exist.
      val = backend.persistence_layer.get_row_list(tablename, val)
      if not op(val, where_value): # for operator.contains, op(a,b) means 'b in a': so need to switch args.
        return False
  return True

def convert_row_from_codes_to_values(row, M_c):
  """
  Helper function to convert a row from its 'code' (as it's stored in T) to its 'value'
  (the human-understandable value).
  """
  ret = []
  for cidx, code in enumerate(row): 
    if not numpy.isnan(code) and not code=='nan':
      ret.append(du.convert_code_to_value(M_c, cidx, code))
    else:
      ret.append(code)
  return tuple(ret)

def filter_and_impute_rows(where_conditions, T, M_c, X_L_list, X_D_list, engine, queries,
                           impute_confidence, numsamples, tablename):
    """
    impute_confidence: if None, don't impute. otherwise, this is the imput confidence
    Iterate through all rows of T, convert codes to values, filter by all predicates in where clause,
    and fill in imputed values.
    """
    filtered_rows = list()
    if impute_confidence is not None:
      t_array = numpy.array(T, dtype=float)
      query_col_indicies = [query[1][0] for query in queries[1:]]
    for row_id, T_row in enumerate(T):
      row_values = convert_row_from_codes_to_values(T_row, M_c) ## Convert row from codes to values

      if is_row_valid(row_id, row_values, where_conditions, M_c, X_L_list, X_D_list, T, engine, tablename, numsamples): ## Where clause filtering.
        if impute_confidence is not None:
          ## Determine which values are 'nan', which need to be imputed.
          ## Only impute columns in 'query_colnames'
          for col_id in query_col_indicies:
            if numpy.isnan(t_array[row_id, col_id]):
              # Found missing value! Try to fill it in.
              # row_id, col_id is Q. Y is givens: All non-nan values in this row
              Y = [(row_id, cidx, t_array[row_id, cidx]) for cidx in M_c['name_to_idx'].values() \
                   if not numpy.isnan(t_array[row_id, cidx])]
              code = utils.infer(M_c, X_L_list, X_D_list, Y, row_id, col_id, numsamples,
                                 impute_confidence, engine)
              if code is not None:
                # Inferred successfully! Fill in the new value.
                value = du.convert_code_to_value(M_c, col_id, code)
                row_values = list(row_values)
                row_values[col_id] = value
                row_values = tuple(row_values)
        filtered_rows.append((row_id, row_values))

    return filtered_rows

def order_rows(rows, order_by, M_c, X_L_list, X_D_list, T, engine, column_lists, numsamples):
  ##TODO deprecate one of these functions
  """Input: rows are list of (row_id, row_values) tuples."""
  if not order_by:
      return rows
  rows = _order_by(rows, order_by, M_c, X_L_list, X_D_list, T, engine, numsamples)
  return rows

def _order_by(filtered_values, function_list, M_c, X_L_list, X_D_list, T, engine, numsamples):
  """
  Return the original data tuples, but sorted by the given functions.
  The data_tuples must contain all __original__ data because you can order by
  data that won't end up in the final result set.
  """
  if len(filtered_values) == 0 or not function_list:
    return filtered_values

  scored_data_tuples = list() ## Entries are (score, data_tuple)
  for row_id, data_tuple in filtered_values:
    ## Apply each function to each data_tuple to get a #functions-length tuple of scores.
    scores = []
    for (f, args, desc) in function_list:
      score = f(args, row_id, data_tuple, M_c, X_L_list, X_D_list, T, engine, numsamples)
      if desc:
        score *= -1
      scores.append(score)
    scored_data_tuples.append((tuple(scores), (row_id, data_tuple)))
  scored_data_tuples.sort(key=lambda tup: tup[0], reverse=False)

  return [tup[1] for tup in scored_data_tuples]


def compute_result_and_limit(rows, limit, queries, M_c, X_L_list, X_D_list, T, engine, numsamples):
  data = []
  row_count = 0

  # Compute aggregate functions just once, then cache them.
  aggregate_cache = dict()
  for query_idx, (query_function, query_args, aggregate) in enumerate(queries):
    if aggregate:
      aggregate_cache[query_idx] = query_function(query_args, None, None, M_c, X_L_list, X_D_list, T, engine, numsamples)

  # Only return one row if all aggregate functions (row_id will never be aggregate, so subtract 1 and don't return it).
  assert queries[0][0] == functions._row_id
  if len(aggregate_cache) == len(queries) - 1:
    limit = 1

  # Iterate through data table, calling each query_function to fill in the output values.
  for row_id, row_values in rows:
    ret_row = []
    for query_idx, (query_function, query_args, aggregate) in enumerate(queries):
      if aggregate:
        ret_row.append(aggregate_cache[query_idx])
      else:
        ret_row.append(query_function(query_args, row_id, row_values, M_c, X_L_list, X_D_list, T, engine, numsamples))
    data.append(tuple(ret_row))
    row_count += 1
    if row_count >= limit:
      break
  return data

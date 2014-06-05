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

def evaluate_where_on_row(row_idx, row, where_conditions, M_c, X_L_list, X_D_list, T, engine, tablename, numsamples, impute_confidence):
  """
  Helper function that applies WHERE conditions to row, returning False if row doesn't satisfy where
  clause, and the list of function results if it does satisfy the where clause.
  """
  function_values = []
  for ((func, f_args), op, val) in where_conditions:
    if func == functions._column and f_args[1] != None and numpy.isnan(T[row_idx][f_args[0]]):
      col_idx = f_args[0]
      confidence = f_args[1]
      ## need to do predictive sampling to evaluate where condition with confidence
      ## TODO: easier way to do this would be to call impute on backend, but would need to change
      ## crosscat so that impute_and_confidence could also return the original samples, or evaluate
      ## a whereclause.
      Y = [(row_idx, cidx, row[cidx]) for cidx in M_c['name_to_idx'].values() \
           if not numpy.isnan(T[row_idx][cidx])]      
      samples = engine.call_backend('simple_predictive_sample',
                   dict(M_c=M_c, X_L=X_L_list, X_D=X_D_list, Y=Y, Q=[[row_idx,col_idx]], n=numsamples))
      samples_satisfying_where = 0
      for sample in samples:
        value = du.convert_code_to_value(M_c, col_idx, sample[0])
        if op(value, val):
          samples_satisfying_where += 1
      if float(samples_satisfying_where)/len(samples) >= confidence:
        # Where clause is satisfied! Now, generate impute summary.
        imputed_code, imputation_confidence = utils.get_imputation_and_confidence_from_samples(
          M_c, X_L_list[0], col_idx, samples)
        if imputed_code is not None:
          imputed_value = du.convert_code_to_value(M_c, col_idx, imputed_code)
        else:
          imputed_value = T[row_idx][col_idx]
        function_values.append(imputed_value)
      else:
        return False
    else:
      where_value = func(f_args, row_idx, row, M_c, X_L_list, X_D_list, T, engine, numsamples)        
      if func == functions._row_id:
        # val should be a row list name in this case. look up the row list, and set val to be the list of
        # row indices in the row list. Throws BayesDBRowListDoesNotExistError if row list does not exist.
        val = engine.persistence_layer.get_row_list(tablename, val)
        if op(val, where_value): # for operator.contains, op(a,b) means 'b in a': so need to switch args.
          function_values.append(where_value)
        else:
          return False
      else:
        # Normal, most common condition.
        if op(where_value, val):
          function_values.append(where_value)
        else:
          return False
  return []

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

def check_if_functions_need_models(queries, tablename, order_by, where_conditions):
  """
  If there are no models, make sure that we aren't using functions that require models.
  TODO: make this less hardcoded
  """
  blacklisted_functions = [functions._similarity, functions._row_typicality, functions._col_typicality, functions._probability]
  used_functions = [q[0] for q in queries] + [w[0] for w in where_conditions] + [x[0] for x in order_by]
  for bf in blacklisted_functions:
    if bf in queries:
      raise utils.BayesDBNoModelsError(tablename)

###### TODO: UNUSED          
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

      if False != evaluate_where_on_row(row_id, row_values, where_conditions, M_c, X_L_list, X_D_list, T, engine, tablename, numsamples, impute_confidence): ## Where clause filtering.
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


####### TODO: UNUSED
def order_rows(rows, order_by, M_c, X_L_list, X_D_list, T, engine, column_lists, numsamples):
  ##TODO deprecate one of these functions
  """Input: rows are list of (row_id, row_values) tuples."""
  if not order_by:
      return rows
  rows = _order_by(rows, order_by, M_c, X_L_list, X_D_list, T, engine, numsamples)
  return rows

####### TODO: UNUSED
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

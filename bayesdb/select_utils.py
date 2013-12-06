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
import crosscat.utils.data_utils as du

import pylab
import matplotlib.cm


def get_conditions_from_whereclause(whereclause):
  ## Create conds: the list of conditions in the whereclause.
  ## List of (c_idx, op, val) tuples.
  conds = list() 
  if len(whereclause) > 0:
    conditions = whereclause.split(',')
    ## Order matters: need <= and >= before < and > and =.
    operator_list = ['<=', '>=', '=', '>', '<']
    operator_map = {'<=': operator.le, '<': operator.lt, '=': operator.eq, '>': operator.gt, '>=': operator.ge}
    for condition in conditions:
      for operator_str in operator_list:
        if operator_str in condition:
          op_str = operator_str
          op = operator_map[op_str]
          break
      vals = condition.split(op_str)
      column = vals[0].strip()

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

      c_idx = M_c['name_to_idx'][column]
      conds.append((c_idx, op, val))
  return conds

def is_row_valid(idx, row, where_conditions):
 """Helper function that applies WHERE conditions to row, returning True if row satisfies where clause."""
  for (c_idx, op, val) in where_conditions:
    if type(row[c_idx]) == str or type(row[c_idx]) == unicode:
      return op(row[c_idx].lower(), val)
    else:
      return op(row[c_idx], val)
  return True

def get_queries_from_columnstring(columnstring):
    """
    Iterate through the columnstring portion of the input, and generate the query list.
    queries is a list of (query_type, query) tuples, where query_type is: row_id, column, probability, similarity.
    For row_id: query is ignored (so it is None).
    For column: query is a c_idx.
    For probability: query is a (c_idx, value) tuple.
    For similarity: query is a (target_row_id, target_column) tuple.
    """
    query_colnames = [colname.strip() for colname in column_string_splitter(columnstring)]
    queries = []
    aggregates_only = True
    for idx, colname in enumerate(query_colnames):
      p = parse_probability(colname)
      if p is not None:
        queries.append(('probability', p))
        continue

      s = parse_similarity(colname, M_c, T)
      if s is not None:
        queries.append(('similarity', s))
        aggregates_only = False
        continue

      if parse_row_typicality(colname):
        queries.append(('row_typicality', None))
        aggregates_only = False        
        continue

      c = parse_column_typicality(colname, M_c)
      if c is not None:
        c_idx = c
        queries.append(('col_typicality', c_idx))
        continue

      ## Check if predictive probability query
      ## TODO: demo (last priority)

      ## Check if mutual information query - AGGREGATE
      m = parse_mutual_information(colname, M_c)
      if m is not None:
        queries.append(('mutual_information', m))
        continue

      ## If none of above query types matched, then this is a normal column query.
      queries.append(('column', M_c['name_to_idx'][colname]))
      aggregates_only = False
      
    ## Always return row_id as the first column.
    query_colnames = ['row_id'] + query_colnames
    queries = [('row_id', None)] + queries
    
    return queries, query_colnames, aggregates_only

def convert_row(row, M_c):
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

def filter_and_impute_rows(T, M_c, imputations_dict):
    ## Iterate through all rows of T, convert codes to values, filter by all predicates in where clause,
    ## and fill in imputed values.
    filtered_rows = list()
    for row_id, T_row in enumerate(T):
      row_values = utils.convert_row(T_row, M_c) ## Convert row from codes to values
      if utils.is_row_valid(row_id, row_values, where_conditions): ## Where clause filtering.
        if imputations_dict and len(imputations_dict[row_id]) > 0:
          ## Fill in any imputed values.
          for col_idx, value in imputations_dict[row_id].items():
            row_values = list(row_values)
            row_values[col_idx] = '*' + str(value)
            row_values = tuple(row_values)
        filtered_rows.append((row_id, row_values))

def order_rows(rows, order_by):
  """Input: rows are list of (row_id, row_values) tuples."""
  if not order_by:
      return rows
  ## Step 1: get appropriate functions. Examples are 'column' and 'similarity'.
  function_list = list()
  for orderable in order_by:
    function_name, args_dict = orderable
    args_dict['M_c'] = M_c
    args_dict['X_L_list'] = X_L_list
    args_dict['X_D_list'] = X_D_list
    args_dict['T'] = T
    ## TODO: use something more understandable and less brittle than getattr here.
    method = getattr(self, '_get_%s_function' % function_name)
    argnames = inspect.getargspec(method)[0]
    args = [args_dict[argname] for argname in argnames if argname in args_dict]
    function = method(*args)
    if args_dict['desc']:
      function = lambda row_id, data_values: -1 * function(row_id, data_values)
    function_list.append(function)
  ## Step 2: call order by.
  rows = self._order_by(rows, function_list)
  return rows  

def compute_result_and_limit(rows, limit, queries, M_c, backend):
  data = []
  row_count = 0
  for row_id, row_values in filtered_rows:
    ret_row = []
    for (query_type, query) in queries:
      if query_type == 'row_id':
        ret_row.append(row_id)
      elif query_type == 'column':
        col_idx = query
        val = row_values[col_idx]
        ret_row.append(val)
      elif query_type == 'probability':
        c_idx, value = query
        if M_c['column_metadata'][c_idx]['code_to_value']:
          val = float(M_c['column_metadata'][c_idx]['code_to_value'][str(value)])
        else:
          val = value
        Q = [(len(X_D_list[0][0])+1, c_idx, val)] ## row is set to 1 + max row, instead of this row.
        prob = math.exp(self.backend.simple_predictive_probability_multistate(M_c, X_L_list, X_D_list, Y, Q))
        ret_row.append(prob)
      elif query_type == 'similarity':
        target_row_id, target_column = query
        sim = self.backend.similarity(M_c, X_L_list, X_D_list, row_id, target_row_id, target_column)
        ret_row.append(sim)
      elif query_type == 'row_typicality':
        anom = self.backend.row_structural_typicality(X_L_list, X_D_list, row_id)
        ret_row.append(anom)
      elif query_type == 'col_typicality':
        c_idx = query
        anom = self.backend.column_structural_typicality(X_L_list, c_idx)
        ret_row.append(anom)
      elif query_type == 'predictive_probability':
        c_idx = query
        ## WARNING: this backend call doesn't work for multinomial
        ## TODO: need to test
        Q = [(row_id, c_idx, du.convert_value_to_code(M_c, c_idx, T[row_id][c_idx]))]
        Y = []
        prob = math.exp(self.backend.simple_predictive_probability_multistate(M_c, X_L_list, X_D_list, Y, Q))
        ret_row.append(prob)
      elif query_type == 'mutual_information':
        c_idx1, c_idx2 = query
        mutual_info, linfoot = self.backend.mutual_information(M_c, X_L_list, X_D_list, [(c_idx1, c_idx2)])
        mutual_info = numpy.mean(mutual_info)
        ret_row.append(mutual_info)

    data.append(tuple(ret_row))
    row_count += 1
    if row_count >= limit:
      break

#################################
# function parsing code
#################################

def parse_probability(colname, M_c):
  prob_match = re.search(r"""
      probability\s*
      \(\s*
      (?P<column>[^\s]+)\s*=\s*(?P<value>[^\s]+)
      \s*\)
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
  similarity_match = re.search(r"""
      similarity\s+to\s+
      (?P<rowid>[^\s]+)
      (\s+with\s+respect\s+to\s+(?P<column>[^\s]+))?
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
        ## Instead of specifying an integer for rowid, you can specify a where clause.
        where_vals = rowid.split('=')
        where_colname = where_vals[0]
        where_val = where_vals[1]
        if type(where_val) == str or type(where_val) == unicode:
          where_val = ast.literal_eval(where_val)
        ## Look up the row_id where this column has this value!
        c_idx = M_c['name_to_idx'][where_colname.lower()]
        for row_id, T_row in enumerate(T):
          row_values = utils.convert_row(T_row, M_c)
          if row_values[c_idx] == where_val:
            target_row_id = row_id
            break

      if similarity_match.group('column'):
          target_column = similarity_match.group('column').strip()
      else:
          target_column = None

      return target_row_id, target_column
  else:
      return None

def parse_row_typicality(colname):
    row_typicality_match = re.search(r"""
        row_typicality
    """, colname, re.VERBOSE | re.IGNORECASE)
    if row_typicality_match:
        return True
    else:
        return None

def parse_col_typicality(colname, M_c):
  col_typicality_match = re.search(r"""
      col_typicality\s*\(\s*
      (?P<column>[^\s]+)
      \s*\)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if col_typicality_match:
      colname = col_typicality_match.group('column').strip()
      return M_c['name_to_idx'][colname]

def parse_mutual_information(colname, M_c):
  mutual_information_match = re.search(r"""
      mutual_information\s*\(\s*
      (?P<col1>[^\s]+)
      \s*,\s*
      (?P<col2>[^\s]+)
      \s*\)
  """, colname, re.VERBOSE | re.IGNORECASE)
  if mutual_information_match:
      col1 = mutual_information_match.group('col1')
      col2 = mutual_information_match.group('col2')
      col1, col2 = M_c['name_to_idx'][col1], M_c['name_to_idx'][col2]
      return col1, col2
  else:
      return None

    

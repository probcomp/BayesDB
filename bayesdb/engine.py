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

import inspect
import os
import pickle
import json
import datetime
import re
import operator
import copy
import math
import ast
#
import pylab
import numpy
import matplotlib.cm
from collections import defaultdict
#
import crosscat.utils.api_utils as au
import crosscat.utils.data_utils as du
import bayesdb.settings as S

from crosscat.CrossCatClient import get_CrossCatClient
from persistence_layer import PersistenceLayer
import utils

class Engine(object):
  def __init__(self, engine_type='local', **kwargs):
    self.backend = get_CrossCatClient(engine_type, **kwargs)
    self.persistence_layer = PersistenceLayer()

  def start_from_scratch(self):
    self.persistence_layer.start_from_scratch()
    return 'Started db from scratch.'

  def drop_and_load_db(self, filename):
    self.persistence_layer.drop_and_load_db(filename)
    return 'Dropped and loaded DB.'

  def drop_tablename(self, tablename):
    """Delete table by tablename."""
    return self.persistence_layer.drop_btable(tablename)

  def delete_chain(self, tablename, chain_index):
     """Delete one chain."""
     return self.persistence_layer.delete_chain(tablename)

  def update_datatypes(self, tablename, mappings):
    """
    mappings is a dict of column name to 'continuous', 'multinomial',
    or an int, which signifies multinomial of a specific type.
    TODO: FIX HACKS. Current works by reloading all the data from csv,
    and it ignores multinomials' specific number of outcomes.
    Also, disastrous things may happen if you update a schema after creating models.
    """
    max_chainid = self.persistence_layer.get_max_chain_id(tablename)
    if max_chainid is not None:
      return 'Error: cannot update datatypes after models have already been created. Please create a new table.'
    
    # First, get existing cctypes, and T, M_c, and M_r.    
    cctypes = self.persistence_layer.get_cctypes(tablename)
    m_c, m_r, t = self.persistence_layer.get_metadata_and_table(tablename)
    
    # Now, update cctypes, T, M_c, and M_r
    for col, mapping in mappings.items():
      ## TODO: fix this hack! See method's docstring.
      if type(mapping) == int:
        mapping = 'multinomial'
      cctypes[m_c['name_to_idx'][col]] = mapping
    t, m_r, m_c, header = du.read_data_objects(csv_abs_path, cctypes=cctypes)

    # Now, put cctypes, T, M_c, and M_r back into the DB
    self.persistence_layer.update_cctypes(tablename, cctypes)
    self.persistence_layer.update_metadata_and_table(tablename, M_r, M_c, T)

    colnames = [m_c['idx_to_name'][str(idx)] for idx in range(len(m_c['idx_to_name']))]
    return dict(columns=colnames, data=[cctypes], message='Updated schema:\n')

  def _guess_schema(self, header, values, crosscat_column_types, colnames):
    """Guess the schema. Complete the given crosscat_column_types, which may have missing data, into cctypes
    Also make the corresponding postgres column types."""
    postgres_coltypes = []
    cctypes = []
    column_data_lookup = dict(zip(header, numpy.array(values).T))
    have_column_tpes = type(crosscat_column_types) == dict
    for colname in colnames:
      if have_column_tpes and colname in crosscat_column_types:
        cctype = crosscat_column_types[colname]
      else:
        column_data = column_data_lookup[colname]
        cctype = du.guess_column_type(column_data)
        # cctype = 'continuous'
      cctypes.append(cctype)
      if cctype == 'ignore':
        postgres_coltypes.append('varchar(1000)')
      elif cctype == 'continuous':
        postgres_coltypes.append('float8')
      elif cctype == 'multinomial':
        postgres_coltypes.append('varchar(1000)')
    return postgres_coltypes, cctypes
        
  def create_btable(self, tablename, csv, crosscat_column_types):
    """Upload a csv table to the predictive db.
    Crosscat_column_types must be a dictionary mapping column names
    to either 'ignore', 'continuous', or 'multinomial'. Not every
    column name must be present in the dictionary: default is continuous."""
    # First, test if table with this name already exists, and fail if it does
    if self.persistence_layer.check_if_table_exists(tablename):
      raise Exception('Error: btable with that name already exists.')
    
    csv_abs_path = self.persistence_layer.write_csv(tablename, csv)

    # Parse column names to create table
    csv = csv.replace('\r', '')
    colnames = csv.split('\n')[0].split(',')

    # Guess schema and create table
    header, values = du.read_csv(csv_abs_path, has_header=True)
    postgres_coltypes, cctypes = self._guess_schema(header, values, crosscat_column_types, colnames)
    self.persistence_layer.create_btable_from_csv(tablename, csv_abs_path, cctypes, postgres_coltypes, colnames)

    return dict(columns=colnames, data=[cctypes], message='Created btable %s. Inferred schema:' % tablename)

  def export_samples(self, tablename):
    """Opposite of import samples! Save a pickled version of X_L_list, X_D_list, M_c, and T."""
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    return dict(M_c=M_c, M_r=M_r, T=T, X_L_list=X_L_list, X_D_list=X_D_list)

  def import_samples(self, tablename, X_L_list, X_D_list, M_c, T, iterations=0):
    """Import these samples as if they are new chains"""
    result = self.persistence_layer.add_samples(tablename, X_L_list, X_D_list, iterations)
    if result == 0:
      return dict(message="Successfully imported %d samples." % len(X_L_list))
    else:
      return dict(message="Error importing samples.")
    
  def create_models(self, tablename, n_chains):
    """Call initialize n_chains times."""
    # Get t, m_c, and m_r, and tableid
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    max_chainid = self.persistence_layer.get_max_chain_id(tablename)

    # Call initialize on backend
    states_by_chain = list()
    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['M_r'] = M_r
    args_dict['T'] = T
    for chain_index in range(max_chainid, n_chains + max_chainid):
      x_l_prime, x_d_prime = self.backend.initialize(M_c, M_r, T)
      states_by_chain.append((x_l_prime, x_d_prime))

    # Insert results into persistence layer
    self.persistence_layer.insert_models(tablename, states_by_chain)

  def analyze(self, tablename, chain_index=1, iterations=2, wait=False):
    """Run analyze for the selected table. chain_index may be 'all'."""
    # Get M_c, T, X_L, and X_D from database
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    
    if (str(chain_index).upper() == 'ALL'):
      chainids = self.persistence_layer.get_chain_ids(tablename)
      print('chainids: %s' % chainids)
    else:
      chainids = [chain_index]

    chainid_iteration_info = list()
    # p_list = []
    for chainid in chainids:
      iters = self._analyze_helper(tablename, M_c, T, chainid, iterations)
      chainid_iteration_info.append('Chain %d: %d iterations' % (chainid, iters))
    #   from multiprocessing import Process
    #   p = Process(target=self._analyze_helper,
    #               args=(tableid, M_c, T, chainid, iterations, self.BACKEND_URI))
    #   p_list.append(p)
    #   p.start()
    # if wait:
    #   for p in p_list:
    #     p.join()
    return dict(message=', '.join(chainid_iteration_info))

  def infer(self, tablename, columnstring, newtablename, confidence, whereclause, limit, numsamples, order_by=False):
    """Impute missing values.
    Sample INFER: INFER columnstring FROM tablename WHERE whereclause WITH confidence LIMIT limit;
    Sample INFER INTO: INFER columnstring FROM tablename WHERE whereclause WITH confidence INTO newtablename LIMIT limit;
    Argument newtablename == null/emptystring if we don't want to do INTO
    """
    # TODO: actually impute only missing values, instead of all values.
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    numrows = len(T)

    t_array = numpy.array(T, dtype=float)
    name_to_idx = M_c['name_to_idx']

    if '*' in columnstring:
      col_indices = name_to_idx.values()
    else:
      colnames = [colname.strip() for colname in columnstring.split(',')]
      col_indices = [name_to_idx[colname] for colname in colnames]
      
    Q = []
    for row_idx in range(numrows):
      for col_idx in col_indices:
        if numpy.isnan(t_array[row_idx, col_idx]):
          Q.append([row_idx, col_idx])

    # FIXME: the purpose of the whereclause is to specify 'given'
    #        p(missing_value | X_L, X_D, whereclause)
    ## TODO: should all observed values besides the ones being imputed be givens?
    if whereclause=="" or '=' not in whereclause:
      Y = None
    else:
      varlist = [[c.strip() for c in b.split('=')] for b in whereclause.split('AND')]
      Y = [(numrows+1, name_to_idx[colname], colval) for colname, colval in varlist]
      Y = [(r, c, du.convert_value_to_code(M_c, c, colval)) for r,c,colval in Y]

    # Call backend
    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['X_L'] = X_L_list
    args_dict['X_D'] = X_D_list
    args_dict['Y'] = Y # givens
    args_dict['n'] = numsamples
    counter = 0
    ret = []
    for q in Q:
      args_dict['Q'] = q # querys
      out = self.backend.impute_and_confidence(M_c, X_L_list, X_D_list, Y, [q], numsamples)
      value, conf = out
      if conf >= confidence:
        row_idx = q[0]
        col_idx = q[1]
        ret.append((row_idx, col_idx, value))
        counter += 1
        if counter >= limit:
          break
    imputations_list = [(r, c, du.convert_code_to_value(M_c, c, code)) for r,c,code in ret]
    ## Convert into dict with r,c keys
    imputations_dict = defaultdict(dict)
    for r,c,val in imputations_list:
      imputations_dict[r][c] = val
    ret = self.select(tablename, columnstring, whereclause, limit, order_by=order_by, imputations_dict=imputations_dict)
    return ret

  def select(self, tablename, columnstring, whereclause, limit, order_by, imputations_dict=None):
    """
    Our own homebrewed select query.
    First, reads codes from T and converts them to values.
    Then, filters the values based on the where clause.
    Then, fills in all imputed values, if applicable.
    Then, orders by the given order_by functions.
    Then, computes the queried values requested by the column string.

    One refactoring option: you could try generating a list of all functions that will be needed, either
    for selecting or for ordering. Then compute those and add them to the data tuples. Then just do the
    order by as if you're doing it exclusively on columns. The only downside is that now if there isn't an
    order by, but there is a limit, then we computed a large number of extra functions.
    """
    probability_query = False ## probability_query is True if at least one of the queries is for probability.
    data_query = False ## data_query is True if at least one of the queries is for raw data.
    similarity_query = False
    typicality_query = False
    mutual_information_query = False
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)

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

    ## Iterate through the columnstring portion of the input, and generate the query list.
    ## queries is a list of (query_type, query) tuples, where query_type is: row_id, column, probability, similarity.
    ## For row_id: query is ignored (so it is None).
    ## For column: query is a c_idx.
    ## For probability: query is a (c_idx, value) tuple.
    ## For similarity: query is a (target_row_id, target_column) tuple.
    ##
    ## TODO: Special case for SELECT *: should this be refactored to support selecting * as well as other functions?
    if '*' in columnstring:
      query_colnames = []
      queries = []
      data_query = True
      for idx in range(len(M_c['name_to_idx'].keys())):
        queries.append(('column', idx))
        query_colnames.append(M_c['idx_to_name'][str(idx)])
    else:
      query_colnames = [colname.strip() for colname in utils.column_string_splitter(columnstring)]
      queries = []
      for idx, colname in enumerate(query_colnames):
        ## Check if probability query
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
          queries.append(('probability', (c_idx, value)))
          probability_query = True
          continue

        ## Check if similarity query
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
                
            queries.append(('similarity', (target_row_id, target_column)))
            similarity_query = True
            continue

        ## Check if row structural anomalousness/typicality query
        row_typicality_match = re.search(r"""
            row_typicality
        """, colname, re.VERBOSE | re.IGNORECASE)
        if row_typicality_match:
            queries.append(('row_typicality', None))
            typicality_query = True
            continue

        ## Check if col structural typicality/typicality query
        col_typicality_match = re.search(r"""
            col_typicality\s*\(\s*
            (?P<column>[^\s]+)
            \s*\)
        """, colname, re.VERBOSE | re.IGNORECASE)
        if col_typicality_match:
            colname = col_typicality_match.group('column').strip()
            queries.append(('col_typicality', M_c['name_to_idx'][colname]))
            typicality_query = True
            continue
            
        ## Check if predictive probability query
        ## TODO: demo (last priority)

        ## Check if mutual information query - AGGREGATE
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
            queries.append(('mutual_information', (M_c['name_to_idx'][col1], M_c['name_to_idx'][col2])))
            mutual_information_query = True
            continue

        ## If none of above query types matched, then this is a normal column query.
        queries.append(('column', M_c['name_to_idx'][colname]))
        data_query = True

    ## Always return row_id as the first column.
    query_colnames = ['row_id'] + query_colnames
    queries = [('row_id', None)] + queries

    ## Helper function that applies WHERE conditions to row, returning True if row satisfies where clause.
    def is_row_valid(idx, row):
      for (c_idx, op, val) in conds:
        if type(row[c_idx]) == str or type(row[c_idx]) == unicode:
          return op(row[c_idx].lower(), val)
        else:
          return op(row[c_idx], val)
      return True

    ## If probability query: get latent states, and simple predictive probability givens (Y).
    ## TODO: Pretty sure this is the wrong way to get Y.
    if probability_query or similarity_query or order_by or typicality_query or mutual_information_query:
      X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    Y = None
    #if probability_query:
      #if whereclause=="" or '=' not in whereclause:
          #Y = None
      '''
      else:
        varlist = [[c.strip() for c in b.split('=')] for b in whereclause.split('AND')]
        Y = [(numrows+1, name_to_idx[colname], colval) for colname, colval in varlist]
        # map values to codes
        Y = [(r, c, du.convert_value_to_code(M_c, c, colval)) for r,c,colval in Y]
      '''

    ## If there are only aggregate values, then only return one row.
    ## TODO: is this actually right? Or is probability also a function of row? If so: get rid of this.
    aggregates_only = reduce(lambda v,q: (q[0] == 'probability' or \
                                          q[0] == 'col_typicality' or \
                                          q[0] == 'mutual_information') and v, queries[1:], True)
    if aggregates_only:
      limit = 1

    ## Iterate through all rows of T, convert codes to values, filter by all predicates in where clause,
    ## and fill in imputed values.
    filtered_values = list()
    for row_id, T_row in enumerate(T):
      row_values = utils.convert_row(T_row, M_c) ## Convert row from codes to values
      if is_row_valid(row_id, row_values): ## Where clause filtering.
        if imputations_dict and len(imputations_dict[row_id]) > 0:
          ## Fill in any imputed values.
          for col_idx, value in imputations_dict[row_id].items():
            row_values = list(row_values)
            row_values[col_idx] = '*' + str(value)
            row_values = tuple(row_values)
        filtered_values.append((row_id, row_values))

    ## Apply order by, if applicable.
    if order_by:
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
      filtered_values = self._order_by(filtered_values, function_list)

    ## Now: generate result set by getting the desired elements of each row, iterating through queries.
    data = []
    row_count = 0
    for row_id, row_values in filtered_values:
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

    ## Prepare for return
    ret = dict(message='', data=data, columns=query_colnames)
    return ret

  def _get_column_function(self, column, M_c):
    """
    Returns a function of the form required by order_by that returns the column value.
    """
    col_idx = M_c['name_to_idx'][column]
    return lambda row_id, data_values: data_values[col_idx]

  def _get_similarity_function(self, target_column, target_row_id, X_L_list, X_D_list, M_c, T):
    """
    Call this function to get a version of similarity as a function of only (row_id, data_values).
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
        row_values = utils.convert_row(T_row, M_c)
        if row_values[c_idx] == where_val:
          target_row_id = row_id
          break
    return lambda row_id, data_values: self.backend.similarity(M_c, X_L_list, X_D_list, row_id, target_row_id, target_column)

  def _order_by(self, filtered_values, functions):
    """
    Return the original data tuples, but sorted by the given functions.
    functions is an iterable of functions that take only data_tuple as an argument.
    The data_tuples must contain all __original__ data because you can order by
    data that won't end up in the final result set.
    """
    if len(filtered_values) == 0 or not functions:
      return filtered_values
    
    scored_data_tuples = list() ## Entries are (score, data_tuple)
    for row_id, data_tuple in filtered_values:
      ## Apply each function to each data_tuple to get a #functions-length tuple of scores.
      scores = tuple([func(row_id, data_tuple) for func in functions])
      scored_data_tuples.append((scores, (row_id, data_tuple)))
    scored_data_tuples.sort(key=lambda tup: tup[0], reverse=True)
    return [tup[1] for tup in scored_data_tuples]


  def simulate(self, tablename, columnstring, newtablename, whereclause, numpredictions, order_by):
    """Simple predictive samples. Returns one row per prediction, with all the given and predicted variables."""
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)

    numrows = len(M_r['idx_to_name'])
    name_to_idx = M_c['name_to_idx']

    # parse whereclause
    where_col_idxs_to_vals = dict()
    if whereclause=="" or '=' not in whereclause:
      Y = None
    else:
      varlist = [[c.strip() for c in b.split('=')] for b in whereclause.split('AND')]
      Y = []
      for colname, colval in varlist:
        if type(colval) == str or type(colval) == unicode:
          colval = ast.literal_eval(colval)
        where_col_idxs_to_vals[name_to_idx[colname]] = colval
        Y.append((numrows+1, name_to_idx[colname], colval))

      # map values to codes
      Y = [(r, c, du.convert_value_to_code(M_c, c, colval)) for r,c,colval in Y]

    ## Parse queried columns.
    colnames = [colname.strip() for colname in columnstring.split(',')]
    col_indices = [name_to_idx[colname] for colname in colnames]
    query_col_indices = [idx for idx in col_indices if idx not in where_col_idxs_to_vals.keys()]
    Q = [(numrows+1, col_idx) for col_idx in query_col_indices]

    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['X_L'] = X_L_list
    args_dict['X_D'] = X_D_list
    args_dict['Y'] = Y
    args_dict['Q'] = Q
    args_dict['n'] = numpredictions
    out = self.backend.simple_predictive_sample(M_c, X_L_list, X_D_list, Y, Q, numpredictions)

    # convert to data, columns dict output format
    # map codes to original values
    ## TODO: Add histogram call back in, but on Python client locally!
    #self.create_histogram(M_c, numpy.array(out), columns, col_indices, tablename+'_histogram')
    data = []
    for vals in out:
      row = []
      i = 0
      for idx in col_indices:
        if idx in where_col_idxs_to_vals:
          row.append(where_col_idxs_to_vals[idx])
        else:
          row.append(du.convert_code_to_value(M_c, idx, vals[i]))
          i += 1
      data.append(row)
    ret = {'message': 'Simulated data:', 'columns': colnames, 'data': data}
    return ret

  def write_json_for_table(self, tablename):
    M_c, M_r, t_dict = self.persistence_layer.get_metadata_and_table(tablename)
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    dir=S.path.web_resources_data_dir
    os.system('rm %s/*.json' % dir)
    if M_r is None:
      num_rows = len(X_D_list[0][0])
      row_indices = range(num_rows)
      row_names = map(str, row_indices)
      name_to_idx = dict(zip(row_names, row_indices))
      idx_to_name = dict(zip(row_indices, row_names))
      M_r = dict(name_to_idx=name_to_idx, idx_to_name=idx_to_name)
    #
    for name in M_c['name_to_idx']:
      M_c['name_to_idx'][name] += 1
    M_c = dict(labelToIndex=M_c['name_to_idx'])
    for name in M_r['name_to_idx']:
      M_r['name_to_idx'][name] += 1
      M_r['name_to_idx'][name]  = M_r['name_to_idx'][name]
    M_r = dict(labelToIndex=M_r['name_to_idx'])
    #
    jsonify_and_dump(M_c, 'M_c.json')
    jsonify_and_dump(M_r, 'M_r.json')
    jsonify_and_dump(t_dict, 'T.json')
    #
    for idx, X_L_i in enumerate(X_L_list):
      filename = 'X_L_%s.json' % idx
      X_L_i = (numpy.array(X_L_i['column_partition']['assignments'])+1).tolist()
      X_L_i = dict(columnPartitionAssignments=X_L_i)
      jsonify_and_dump(X_L_i, filename)
    for idx, X_D_i in enumerate(X_D_list):
      filename = 'X_D_%s.json' % idx
      X_D_i = (numpy.array(X_D_i)+1).tolist()
      X_D_i = dict(rowPartitionAssignments=X_D_i)
      jsonify_and_dump(X_D_i, filename)
    json_indices_dict = dict(ids=map(str, range(len(X_D_list))))
    jsonify_and_dump(json_indices_dict, "json_indices")


  def create_histogram(self, M_c, data, columns, mc_col_indices, filename):
    dir=S.path.web_resources_data_dir
    full_filename = os.path.join(dir, filename)
    num_rows = data.shape[0]
    num_cols = data.shape[1]
    #
    pylab.figure()
    # col_i goes from 0 to number of predicted columns
    # mc_col_idx is the original column's index in M_c
    for col_i in range(num_cols):
      mc_col_idx = mc_col_indices[col_i]
      data_i = data[:, col_i]
      ax = pylab.subplot(1, num_cols, col_i, title=columns[col_i])
      if M_c['column_metadata'][mc_col_idx]['modeltype'] == 'normal_inverse_gamma':
        pylab.hist(data_i, orientation='horizontal')
      else:
        str_data = [du.convert_code_to_value(M_c, mc_col_idx, code) for code in data_i]
        unique_labels = list(set(str_data))
        np_str_data = numpy.array(str_data)
        counts = []
        for label in unique_labels:
          counts.append(sum(np_str_data==label))
        num_vals = len(M_c['column_metadata'][mc_col_idx]['code_to_value'])
        rects = pylab.barh(range(num_vals), counts)
        heights = numpy.array([rect.get_height() for rect in rects])
        ax.set_yticks(numpy.arange(num_vals) + heights/2)
        ax.set_yticklabels(unique_labels)
    pylab.tight_layout()
    pylab.savefig(full_filename)

  def estimate_dependence_probabilities(self, tablename, col, confidence, limit, filename, submatrix):
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    return _do_gen_feature_z(X_L_list, X_D_list, M_c, tablename, filename, col, confidence, limit, submatrix)

  def gen_feature_z(self, tablename, filename=None,
                    dir=S.path.web_resources_dir):
    if filename is None:
      filename = tablename + '_feature_z'
    full_filename = os.path.join(dir, filename)
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    return _do_gen_feature_z(X_L_list, X_D_list, M_c,
                             tablename, full_filename)

  def dump_db(self, filename, dir=S.path.web_resources_dir):
    full_filename = os.path.join(dir, filename)
    if filename.endswith('.gz'):
      cmd_str = 'pg_dump %s | gzip > %s' % (dbname, full_filename)
    else:
      cmd_str = 'pg_dump %s > %s' % (dbname, full_filename)
    os.system(cmd_str)
    return dict(message='Database successfully dumped to %s' % full_filename)


  def _analyze_helper(self, tablename, M_c, T, chainid, iterations):
    """Only for one chain."""
    X_L_prime, X_D_prime, prev_iterations = self.persistence_layer.get_chain(tablename, chainid)

    # Call analyze on backend      
    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['T'] = T
    args_dict['X_L'] = X_L_prime
    args_dict['X_D'] = X_D_prime
    # FIXME: allow specification of kernel_list
    args_dict['kernel_list'] = ()
    args_dict['n_steps'] = iterations
    args_dict['c'] = () # Currently ignored by analyze
    args_dict['r'] = () # Currently ignored by analyze
    args_dict['max_iterations'] = -1 # Currently ignored by analyze
    args_dict['max_time'] = -1 # Currently ignored by analyze
    X_L_prime, X_D_prime = self.backend.analyze(M_c, T, X_L_prime, X_D_prime, (), iterations)

    self.persistence_layer.add_samples_for_chain(tablename, X_L_prime, X_D_prime, prev_iterations + iterations, chainid)
    return (prev_iterations + iterations)


def jsonify_and_dump(to_dump, filename):
  dir=S.path.web_resources_data_dir
  full_filename = os.path.join(dir, filename)
  print full_filename
  try:
    with open(full_filename, 'w') as fh:
      json_str = json.dumps(to_dump)
      json_str = json_str.replace("NaN", "0")
      fh.write(json_str)
  except Exception, e:
    print e
  return dict(message="Database successfuly dumped as JSON to %s" % filename)

def _do_gen_feature_z(X_L_list, X_D_list, M_c, tablename='', filename=None, col=None, confidence=None, limit=None, submatrix=False):
    num_cols = len(X_L_list[0]['column_partition']['assignments'])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)
    # extract unordered z_matrix
    num_latent_states = len(X_L_list)
    z_matrix = numpy.zeros((num_cols, num_cols))
    for X_L in X_L_list:
      assignments = X_L['column_partition']['assignments']
      for i in range(num_cols):
        for j in range(num_cols):
          if assignments[i] == assignments[j]:
            z_matrix[i, j] += 1
    z_matrix /= float(num_latent_states)
    
    if col:
      z_column = list(z_matrix[M_c['name_to_idx'][col]])
      data_tuples = zip(z_column, range(num_cols))
      data_tuples.sort(reverse=True)
      if confidence:
        data_tuples = filter(lambda tup: tup[0] >= float(confidence), data_tuples)
      if limit and limit != float("inf"):
        data_tuples = data_tuples[:int(limit)]
      data = [tuple([d[0] for d in data_tuples])]
      columns = [d[1] for d in data_tuples]
      column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]      
      column_names = numpy.array(column_names)
      column_names_reordered = column_names[columns]
      if submatrix:
        z_matrix = z_matrix[columns,:][:,columns]
        z_matrix_reordered = z_matrix
      else:
        return {'data': data, 'columns': column_names_reordered}
    else:
      # hierachically cluster z_matrix
      import hcluster
      Y = hcluster.pdist(z_matrix)
      Z = hcluster.linkage(Y)
      pylab.figure()
      hcluster.dendrogram(Z)
      intify = lambda x: int(x.get_text())
      reorder_indices = map(intify, pylab.gca().get_xticklabels())
      pylab.close()
      # REORDER! 
      z_matrix_reordered = z_matrix[:, reorder_indices][reorder_indices, :]
      column_names_reordered = column_names[reorder_indices]
      
    title = 'Column Dependencies for: %s' % tablename
    if filename:
      utils.plot_feature_z(z_matrix_reordered, column_names_reordered, title, filename)
      
    return dict(
      matrix=z_matrix_reordered,
      column_names=column_names_reordered,
      title=title,
      filename=filename,
      message = "Created column dependency matrix for %s." % tablename
      )

# helper functions
get_name = lambda x: getattr(x, '__name__')
get_Engine_attr = lambda x: getattr(Engine, x)
is_Engine_method_name = lambda x: inspect.ismethod(get_Engine_attr(x))
#
def get_method_names():
    return filter(is_Engine_method_name, dir(Engine))
#
def get_method_name_to_args():
    method_names = get_method_names()
    method_name_to_args = dict()
    for method_name in method_names:
        method = Engine.__dict__[method_name]
        arg_str_list = inspect.getargspec(method).args[1:]
        method_name_to_args[method_name] = arg_str_list
    return method_name_to_args

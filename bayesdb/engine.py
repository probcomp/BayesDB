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

import time
import inspect
import os
import json
import datetime
import re
import operator
import copy
import math
import ast
import sys
import random

import pylab
import numpy
import matplotlib.cm
from collections import defaultdict

import bayesdb.settings as S
from persistence_layer import PersistenceLayer
import api_utils
import data_utils
import utils
import functions
import select_utils
import estimate_columns_utils
import plotting_utils

class Engine(object):
  def __init__(self, crosscat_host=None, crosscat_port=8007, crosscat_engine_type='multiprocessing', **kwargs):
    """ One optional argument that you may find yourself using frequently is seed.
    It defaults to random seed, but for testing/reproduceability purposes you may
    want a deterministic one. """
    
    self.persistence_layer = PersistenceLayer()

    if crosscat_host is None or crosscat_host == 'localhost':
      self.online = False
      
      # Only dependent on CrossCat when you actually instantiate Engine
      # (i.e., allow engine to be imported in order to examine the API, without CrossCat)
      from crosscat.CrossCatClient import get_CrossCatClient
      self.backend = get_CrossCatClient(crosscat_engine_type, **kwargs)
    else:
      self.online = True
      self.hostname = crosscat_host
      self.port = crosscat_port
      self.URI = 'http://' + self.hostname + ':%d' % self.port

  def call_backend(self, method_name, args_dict):
    """
    Helper function used to call the CrossCat backend, whether it is remote or local.
    Accept method name and arguments for that method as input.
    """
    if self.online:
      out, id = api_utils.call(method_name, args_dict, self.URI)
    else:
      method = getattr(self.backend, method_name)
      out = method(**args_dict)
    return out

  def drop_btable(self, tablename):
    """Delete table by tablename."""
    self.persistence_layer.drop_btable(tablename)
    return dict()

  def list_btables(self):
    """Return names of all btables."""
    return dict(list=self.persistence_layer.list_btables())

  def update_schema(self, tablename, mappings):
    """
    mappings is a dict of column name to 'continuous', 'multinomial',
    or an int, which signifies multinomial of a specific type.
    TODO: FIX HACKS. Currently works by reloading all the data from csv,
    and it ignores multinomials' specific number of outcomes.
    Also, disastrous things may happen if you update a schema after creating models.
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    msg = self.persistence_layer.update_schema(tablename, mappings)
    ret = self.show_schema(tablename)
    ret['message'] = 'Updated schema.'
    return ret
    
  def _guess_schema(self, colnames, values, crosscat_column_types):
    # TODO: should this be deleted in favor of using crosscat's datatype guessing?
    # If so, then call data_utils.read_model_data_from_csv(...) in create_btable instead of data_utils.read_csv(...)
    """Guess the schema. Complete the given crosscat_column_types, which may have missing data, into cctypes
    Also make the corresponding postgres column types."""
    postgres_coltypes = []
    cctypes = []
    column_data_lookup = dict(zip(colnames, numpy.array(values).T))
    have_column_tpes = type(crosscat_column_types) == dict
    for colname in colnames:
      if have_column_tpes and colname in crosscat_column_types:
        cctype = crosscat_column_types[colname]
      else:
        column_data = column_data_lookup[colname]
        cctype = data_utils.guess_column_type(column_data)
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
    """Uplooad a csv table to the predictive db.
    Crosscat_column_types must be a dictionary mapping column names
    to either 'ignore', 'continuous', or 'multinomial'. Not every
    column name must be present in the dictionary: default is continuous."""
    ## First, test if table with this name already exists, and fail if it does
    if self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBError('Btable with name %s already exists.' % tablename)
    
    csv_abs_path = self.persistence_layer.write_csv(tablename, csv)

    ## Guess schema and create table
    header, values = data_utils.read_csv(csv_abs_path, has_header=True)
    colnames = [h.lower() for h in header]
    values = data_utils.convert_nans(values)
    postgres_coltypes, cctypes = self._guess_schema(colnames, values, crosscat_column_types)
    self.persistence_layer.create_btable_from_csv(tablename, csv_abs_path, csv, cctypes, postgres_coltypes, colnames)

    return dict(columns=colnames, data=[cctypes], message='Created btable %s. Inferred schema:' % tablename)

  def show_schema(self, tablename):
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    metadata = self.persistence_layer.get_metadata(tablename)
    colnames = utils.get_all_column_names_in_original_order(metadata['M_c'])
    cctypes = metadata['cctypes']
    return dict(columns=colnames, data=[cctypes])

  def save_models(self, tablename):    
    """Opposite of load models! Returns the models, including the contents, which
    the client then saves to disk (in a pickle file)."""
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    return self.persistence_layer.get_models(tablename)

  def load_models(self, tablename, models):
    """Load these models as if they are new models"""
    # Models are stored in the format: dict[model_id] = dict[X_L, X_D, iterations].
    # We just want to pass the values.

    # For backwards compatibility with v0.1, where models are stored in the format:
    # dict[X_L_list, X_D_list, M_c, T]
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    if 'X_L_list' in models:
      print """WARNING! The models you are currently importing are stored in an old format
         (from version 0.1); it is deprecated and may not be supported in future releases.
         Please use "SAVE MODELS" to create an updated copy of your models."""
      
      old_models = models
      models = dict()
      for id, (X_L, X_D) in enumerate(zip(old_models['X_L_list'], old_models['X_D_list'])):
        models[id] = dict(X_L=X_L, X_D=X_D, iterations=500)
      
    result = self.persistence_layer.add_models(tablename, models.values())
    return self.show_models(tablename)

  def drop_models(self, tablename, model_indices=None):
    """Drop the specified models. If model_ids is None or all, drop all models."""
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    self.persistence_layer.drop_models(tablename, model_indices)
    return self.show_models(tablename)
    
  def initialize_models(self, tablename, n_models, model_config=None):
    """
    Initialize n_models models.

    By default, model_config specifies to use the CrossCat model. You may pass 'naive bayes'
    or 'crp mixture' to use those specific models instead. Alternatively, you can pass a custom
    dictionary for model_config, as long as it contains a kernel_list, initializaiton, and
    row_initialization.
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    # Get t, m_c, and m_r, and tableid
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    max_modelid = self.persistence_layer.get_max_model_id(tablename)

    # Set model configuration parameters.
    if type(model_config) == str and model_config.lower() == 'naive bayes':
      model_config = dict(kernel_list=['column_hyperparameters'],
                          initialization='together',
                          row_initialization='together')
    elif type(model_config) == str and model_config.lower() == 'crp mixture':
      model_config = dict(kernel_list=['column_hyperparameters',
                                       'row_partition_hyperparameters',
                                       'row_partition_assignments'],
                          initialization='together',
                          row_initialization='from_the_prior')
    elif type(model_config) != dict or ('kernel_list' not in model_config) or ('initialization' not in model_config) or ('row_initialization' not in model_config):
      # default model_config: crosscat
      model_config = dict(kernel_list=(), # uses default
                          initialization='from_the_prior',
                          row_initialization='from_the_prior')

    # Call initialize on backend
    X_L_list, X_D_list = self.call_backend('initialize',
                                           dict(M_c=M_c, M_r=M_r, T=T, n_chains=n_models,
                                                initialization=model_config['initialization'],
                                                row_initialization=model_config['row_initialization']))

    # If n_models is 1, initialize returns X_L and X_D instead of X_L_list and X_D_list
    if n_models == 1:
      X_L_list = [X_L_list]
      X_D_list = [X_D_list]
    
    model_list = list()    
    for X_L, X_D in zip(X_L_list, X_D_list):
      model_list.append(dict(X_L=X_L, X_D=X_D, iterations=0,
                             column_crp_alpha=[], logscore=[], num_views=[],
                             model_config=model_config))

    # Insert results into persistence layer
    self.persistence_layer.add_models(tablename, model_list)
    return self.show_models(tablename)

  def show_models(self, tablename):
    """Return the current models and their iteration counts."""
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    models = self.persistence_layer.get_models(tablename)
    modelid_iteration_info = list()
    for modelid, model in sorted(models.items(), key=lambda t:t[0]):
      modelid_iteration_info.append((modelid, model['iterations']))
    if len(models) == 0:
      return dict(message="No models for btable %s. Create some with the INITIALIZE MODELS command." % tablename)
    else:
      return dict(models=modelid_iteration_info)

  def show_diagnostics(self, tablename):
    """
    Display diagnostic information for all your models.
    TODO: generate plots of num_views, column_crp_alpha, logscore, and f_z stuff
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    models = self.persistence_layer.get_models(tablename)    
    data = list()
    for modelid, model in sorted(models.items(), key=lambda t:t[0]):
      data.append((modelid, model['iterations'], str(model['model_config'])))
    if len(models) == 0:
      return dict(message="No models for btable %s. Create some with the INITIALIZE MODELS command." % tablename)
    else:
      return dict(columns=['model_id', 'iterations', 'model_config'], data=data)
    

  def analyze(self, tablename, model_indices=None, iterations=None, seconds=None):
    """
    Run analyze for the selected table. model_indices may be 'all' or None to indicate all models.

    Runs for a maximum of iterations 
    
    Previously: this command ran in the same thread as this engine.
    Now: runs each model in its own thread, and does 10 seconds of inference at a time,
    by default. Each thread also has its own crosscat engine instance!
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    if not self.persistence_layer.has_models(tablename):
      raise utils.BayesDBNoModelsError(tablename)
    
    if iterations is None:
      iterations = 1000
    
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    
    max_model_id = self.persistence_layer.get_max_model_id(tablename)
    if max_model_id == -1:
      return dict(message="You must INITIALIZE MODELS before using ANALYZE.")
    models = self.persistence_layer.get_models(tablename)

    if model_indices is None or (str(model_indices).upper() == 'ALL'):
      modelids = sorted(models.keys())
    else:
      assert type(model_indices) == list
      modelids = model_indices

    X_L_list = [models[i]['X_L'] for i in modelids]
    X_D_list = [models[i]['X_D'] for i in modelids]

    first_model = models[modelids[0]]
    if 'kernel_list' in first_model:
      kernel_list = ['kernel_list']
    else:
      kernel_list = () # default kernel list
      
    analyze_args = dict(M_c=M_c, T=T, X_L=X_L_list, X_D=X_D_list, do_diagnostics=True,
                        kernel_list=kernel_list)
    
    analyze_args['n_steps'] = iterations
    if seconds is not None:
      analyze_args['max_time'] = seconds

    X_L_list_prime, X_D_list_prime, diagnostics_dict = self.call_backend('analyze', analyze_args)
    iterations = len(diagnostics_dict['logscore'])
    self.persistence_layer.update_models(tablename, modelids, X_L_list_prime, X_D_list_prime, diagnostics_dict)
    
    ret = self.show_models(tablename)
    ret['message'] = 'Analyze complete.'
    return ret

  def infer(self, tablename, columnstring, newtablename, confidence, whereclause, limit, numsamples, order_by=False, plot=False):
    """Impute missing values.
    Sample INFER: INFER columnstring FROM tablename WHERE whereclause WITH confidence LIMIT limit;
    Sample INFER INTO: INFER columnstring FROM tablename WHERE whereclause WITH confidence INTO newtablename LIMIT limit;
    Argument newtablename == null/emptystring if we don't want to do INTO
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    if not self.persistence_layer.has_models(tablename):
      raise utils.BayesDBNoModelsError(tablename)      
    
    if numsamples is None:
      numsamples=50
      
    return self.select(tablename, columnstring, whereclause, limit, order_by,
                       impute_confidence=confidence, num_impute_samples=numsamples, plot=plot)
    
  def select(self, tablename, columnstring, whereclause, limit, order_by, impute_confidence=None, num_impute_samples=None, plot=False):
    """
    BQL's version of the SQL SELECT query.
    
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
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    column_lists = self.persistence_layer.get_column_lists(tablename)

    # query_colnames is the list of the raw columns/functions from the columnstring, with row_id prepended
    # queries is a list of (query_function, query_args, aggregate) tuples, where 'query_function' is
    #   a function like row_id, column, similarity, or typicality, and 'query_args' are the function-specific
    #   arguments that that function takes (in addition to the normal arguments, like M_c, X_L_list, etc).
    #   aggregate specifies whether that individual function is aggregate or not
    queries, query_colnames = select_utils.get_queries_from_columnstring(columnstring, M_c, T, column_lists)

    # where_conditions is a list of (c_idx, op, val) tuples, e.g. name > 6 -> (0,>,6)
    # TODO: support functions in where_conditions. right now we only support actual column values.
    where_conditions = select_utils.get_conditions_from_whereclause(whereclause, M_c, T)

    # If there are no models, make sure that we aren't using functions that require models.
    # TODO: make this less hardcoded
    if len(X_L_list) == 0:
      blacklisted_functions = [functions._similarity, functions._row_typicality, functions._col_typicality, functions._probability]
      used_functions = [q[0] for q in queries]
      for bf in blacklisted_functions:
        if bf in queries:
          raise utils.BayesDBNoModelsError(tablename)
      if order_by:
        order_by_functions = [x[0] for x in order_by]
        blacklisted_function_names = ['similarity', 'typicality', 'probability', 'predictive probability']        
        for fname in blacklisted_function_names:
          for order_by_f in order_by_functions:
            if fname in order_by_f:
              raise utils.BayesDBNoModelsError(tablename)              

    # List of rows; contains actual data values (not categorical codes, or functions),
    # missing values imputed already, and rows that didn't satsify where clause filtered out.
    filtered_rows = select_utils.filter_and_impute_rows(where_conditions, whereclause, T, M_c, X_L_list, X_D_list, self,
                                                        query_colnames, impute_confidence, num_impute_samples)

    ## TODO: In order to avoid double-calling functions when we both select them and order by them,
    ## we should augment filtered_rows here with all functions that are going to be selected
    ## (and maybe temporarily augmented with all functions that will be ordered only)
    ## If only being selected: then want to compute after ordering...

    # Simply rearranges the order of the rows in filtered_rows according to the order_by query.
    filtered_rows = select_utils.order_rows(filtered_rows, order_by, M_c, X_L_list, X_D_list, T, self)

    # Iterate through each row, compute the queried functions for each row, and limit the number of returned rows.
    data = select_utils.compute_result_and_limit(filtered_rows, limit, queries, M_c, X_L_list, X_D_list, T, self)

    ret = dict(data=data, columns=query_colnames)
    if plot:
      ret['M_c'] = M_c
    return ret

  def simulate(self, tablename, columnstring, newtablename, givens, numpredictions, order_by, plot=False):
    """Simple predictive samples. Returns one row per prediction, with all the given and predicted variables."""
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    if not self.persistence_layer.has_models(tablename):
      raise utils.BayesDBNoModelsError(tablename)            

    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    if len(X_L_list) == 0:
      return {'message': 'You must INITIALIZE MODELS (and highly preferably ANALYZE) before using predictive queries.'}
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)

    numrows = len(M_r['idx_to_name'])
    name_to_idx = M_c['name_to_idx']

    # parse givens
    given_col_idxs_to_vals = dict()
    if givens=="" or '=' not in givens:
      Y = None
    else:
      varlist = [[c.strip() for c in b.split('=')] for b in givens.split('AND')]
      Y = []
      for colname, colval in varlist:
        if type(colval) == str or type(colval) == unicode:
          colval = ast.literal_eval(colval)
        given_col_idxs_to_vals[name_to_idx[colname]] = colval
        Y.append((numrows+1, name_to_idx[colname], colval))

      # map values to codes
      Y = [(r, c, data_utils.convert_value_to_code(M_c, c, colval)) for r,c,colval in Y]

    ## Parse queried columns.
    column_lists = self.persistence_layer.get_column_lists(tablename)
    colnames = utils.column_string_splitter(columnstring, M_c, column_lists)
    colnames = [c.lower() for c in colnames]
    col_indices = [name_to_idx[colname] for colname in colnames]
    query_col_indices = [idx for idx in col_indices if idx not in given_col_idxs_to_vals.keys()]
    Q = [(numrows+1, col_idx) for col_idx in query_col_indices]

    if len(Q) > 0:
      out = self.call_backend('simple_predictive_sample', dict(M_c=M_c, X_L=X_L_list, X_D=X_D_list, Y=Y, Q=Q, n=numpredictions))
    else:
      out = []

    # convert to data, columns dict output format
    # map codes to original values
    data = []
    for vals in out:
      row = []
      i = 0
      for idx in col_indices:
        if idx in given_col_idxs_to_vals:
          row.append(given_col_idxs_to_vals[idx])
        else:
          row.append(data_utils.convert_code_to_value(M_c, idx, vals[i]))
          i += 1
      data.append(row)
      
    ret = {'columns': colnames, 'data': data}
    if plot:
      ret['M_c'] = M_c
    return ret

  def show_column_lists(self, tablename):
    """
    Return a list of all column list names.
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
      
    column_lists = self.persistence_layer.get_column_lists(tablename)
    return dict(columns=list(column_lists.keys()))

  def show_columns(self, tablename, column_list=None):
    """
    Return the specified columnlist. If None, return all columns in original order.
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
      
    if column_list:
      column_names = self.persistence_layer.get_column_list(tablename, column_list)
    else:
      M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)      
      column_names = list(M_c['name_to_idx'].keys())
    return dict(columns=column_names)

  def estimate_columns(self, tablename, columnstring, whereclause, limit, order_by, name=None):
    """
    Return all the column names from the specified table as a list.
    First, columns are filtered based on whether they match the whereclause.
    The whereclause must consist of functions of a single column only.
    Next, the columns are ordered by other functions of a single column.
    Finally, the columns are limited to the specified number.

    ## allowed functions:
    # typicality(centrality)
    # dependence probability to <col>
    # mutual information with <col>
    # correlation with <col>
    """
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    
    if columnstring and len(columnstring) > 0:
      # User has entered the columns to be in the column list.
      column_indices = [M_c['name_to_idx'][colname.lower()] for colname in utils.column_string_splitter(columnstring, M_c, [])]
    else:
      # Start with all columns.
      column_indices = list(M_c['name_to_idx'].values())
    
    ## filter based on where clause
    where_conditions = estimate_columns_utils.get_conditions_from_column_whereclause(whereclause, M_c, T)
    if len(where_conditions) > 0 and len(X_L_list) == 0:
      raise utils.BayesDBNoModelsError(tablename)      
    column_indices = estimate_columns_utils.filter_column_indices(column_indices, where_conditions, M_c, T, X_L_list, X_D_list, self)
    
    ## order
    if order_by and len(X_L_list) == 0:
      raise utils.BayesDBNoModelsError(tablename)      
    column_indices = estimate_columns_utils.order_columns(column_indices, order_by, M_c, X_L_list, X_D_list, T, self)
    
    # limit
    if limit != float('inf'):
      column_indices = column_indices[:limit]

    # convert indices to names
    column_names = [M_c['idx_to_name'][str(idx)] for idx in column_indices]

    # save column list, if given a name to save as
    if name:
      self.persistence_layer.add_column_list(tablename, name, column_names)
    
    return {'columns': column_names}
  
  def estimate_pairwise(self, tablename, function_name, column_list=None, components_name=None, threshold=None):
    if not self.persistence_layer.check_if_table_exists(tablename):
      raise utils.BayesDBInvalidBtableError(tablename)
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    if len(X_L_list) == 0:
      raise utils.BayesDBNoModelsError(tablename)
    
    if column_list:
      column_names = self.persistence_layer.get_column_list(tablename, column_list)
    else:
      column_names = None

    # Do the heavy lifting: generate the matrix itself
    ret = utils.generate_pairwise_matrix(function_name,
                                         X_L_list, X_D_list, M_c, T, tablename,
                                         engine=self, column_names=column_names,
                                         component_threshold=threshold)

    # Add the column lists for connected components, if desired. Overwrites old ones with same name.
    if components_name is not None and threshold is not None:
      components = ret['components']
      component_name_tuples = []
      for i, component in enumerate(components):
        name = "%s_%d" % (components_name, i)
        column_names = [M_c['idx_to_name'][str(idx)] for idx in component]
        self.persistence_layer.add_column_list(tablename, name, column_names)
        component_name_tuples.append((name, column_names))
      ret['column_lists'] = component_name_tuples
        
    return ret

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

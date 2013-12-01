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
#
import pylab
import numpy
import matplotlib.cm
from scipy.stats import pearsonr
from collections import defaultdict
#
import crosscat.utils.api_utils as au
import crosscat.utils.data_utils as du
import bayesdb.settings as S

from crosscat.CrossCatClient import get_CrossCatClient
from _file_persistence_layer import FilePersistenceLayer
from _postgres_persistence_layer import PostgresPersistenceLayer
import utils

class Engine(object):
  def __init__(self, crosscat_engine_type='local', **kwargs):
    self.backend = get_CrossCatClient(crosscat_engine_type, **kwargs)
    #self.persistence_layer = FilePersistenceLayer()
    self.persistence_layer = PostgresPersistenceLayer()

  def start_from_scratch(self):
    self.persistence_layer.start_from_scratch()
    return 'Started db from scratch.'

  def drop_btable(self, tablename):
    """Delete table by tablename."""
    return self.persistence_layer.drop_btable(tablename)

  def list_btables(self):
    """Return names of all btables."""
    return self.persistence_layer.list_btables()

  def delete_model(self, tablename, model_index):
     """Delete one model."""
     return self.persistence_layer.delete_model(tablename)

  def update_datatypes(self, tablename, mappings):
    """
    mappings is a dict of column name to 'continuous', 'multinomial',
    or an int, which signifies multinomial of a specific type.
    TODO: FIX HACKS. Current works by reloading all the data from csv,
    and it ignores multinomials' specific number of outcomes.
    Also, disastrous things may happen if you update a schema after creating models.
    """
    max_modelid = self.persistence_layer.get_max_model_id(tablename)
    if max_modelid is not None:
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
    """Uplooad a csv table to the predictive db.
    Crosscat_column_types must be a dictionary mapping column names
    to either 'ignore', 'continuous', or 'multinomial'. Not every
    column name must be present in the dictionary: default is continuous."""
    ## First, test if table with this name already exists, and fail if it does
    if self.persistence_layer.check_if_table_exists(tablename):
      raise Exception('Error: btable with that name already exists.')
    
    csv_abs_path = self.persistence_layer.write_csv(tablename, csv)

    ## Parse column names to create table
    csv = csv.replace('\r', '')
    colnames = csv.split('\n')[0].split(',')

    ## Guess schema and create table
    header, values = du.read_csv(csv_abs_path, has_header=True)
    postgres_coltypes, cctypes = self._guess_schema(header, values, crosscat_column_types, colnames)
    self.persistence_layer.create_btable_from_csv(tablename, csv_abs_path, cctypes, postgres_coltypes, colnames)

    return dict(columns=colnames, data=[cctypes], message='Created btable %s. Inferred schema:' % tablename)

  def export_models(self, tablename):
    """Opposite of import models! Save a pickled version of X_L_list, X_D_list, M_c, and T."""
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    return dict(M_c=M_c, M_r=M_r, T=T, X_L_list=X_L_list, X_D_list=X_D_list)

  def import_models(self, tablename, X_L_list, X_D_list, M_c, T, iterations=0):
    """Import these models as if they are new models"""
    result = self.persistence_layer.add_models(tablename, X_L_list, X_D_list, iterations)
    if result == 0:
      return dict(message="Successfully imported %d models." % len(X_L_list))
    else:
      return dict(message="Error importing models.")
    
  def create_models(self, tablename, n_models):
    """Call initialize n_models times."""
    # Get t, m_c, and m_r, and tableid
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    max_modelid = self.persistence_layer.get_max_model_id(tablename)

    # Call initialize on backend
    states_by_model = list()
    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['M_r'] = M_r
    args_dict['T'] = T
    for model_index in range(max_modelid, n_models + max_modelid):
      x_l_prime, x_d_prime = self.backend.initialize(M_c, M_r, T)
      states_by_model.append((x_l_prime, x_d_prime))

    # Insert results into persistence layer
    self.persistence_layer.create_models(tablename, states_by_model)

  def analyze(self, tablename, model_index='all', iterations=2, wait=False):
    """Run analyze for the selected table. model_index may be 'all'."""
    # Get M_c, T, X_L, and X_D from database
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    
    if (str(model_index).upper() == 'ALL'):
      modelids = self.persistence_layer.get_model_ids(tablename)
      print('modelids: %s' % modelids)
    else:
      modelids = [model_index]

    modelid_iteration_info = list()
    # p_list = []
    for modelid in modelids:
      iters = self._analyze_helper(tablename, M_c, T, modelid, iterations)
      modelid_iteration_info.append('Model %d: %d iterations' % (modelid, iters))
    #   from multiprocessing import Process
    #   p = Process(target=self._analyze_helper,
    #               args=(tableid, M_c, T, modelid, iterations, self.BACKEND_URI))
    #   p_list.append(p)
    #   p.start()
    # if wait:
    #   for p in p_list:
    #     p.join()
    return dict(message=', '.join(modelid_iteration_info))

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
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    Y = None ## Simple predictive probability givens.

    queries, query_colnames, aggregates_only = utils.get_queries_from_columnstring(columnstring, M_c, T)
    where_conditions = utils.get_conditions_from_whereclause(whereclause)      

    filtered_rows = utils.filter_and_impute_rows(T, M_c, imputations_dict, where_conditions)

    ## TODO: In order to avoid double-calling functions when we both select them and order by them,
    ## we should augment filtered_rows here with all functions that are going to be selected
    ## (and maybe temporarily augmented with all functions that will be ordered only)
    ## If only being selected: then want to compute after ordering...
    
    filtered_rows = utils.order_rows(filtered_rows, order_by, M_c, X_L_list, X_D_list, T, self.backend)
    data = utils.compute_result_and_limit(filtered_rows, limit, queries, M_c, X_L_list, X_D_list, self.backend)
    return dict(message='', data=data, columns=query_colnames)

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
    #self._create_histogram(M_c, numpy.array(out), columns, col_indices, tablename+'_histogram')
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

  def _create_histogram(self, M_c, data, columns, mc_col_indices, filename):
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

  def estimate_columns(self, tablename, whereclause, limit, order_by, name=None):
    raise NotImplementedError()
  
  def estimate_pairwise(self, tablename, function_name, filename, column_list=None):
    ## TODO: implement functionality with column_list
    if column_list is not None:
      raise NotImplementedError()
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    M_c, M_r, T = self.persistence_layer.get_metadata_and_table(tablename)
    return self._do_gen_matrix(function_name, X_L_list, X_D_list, M_c, T, tablename, filename)

  def estimate_dependence_probabilities(self, tablename, col, confidence, limit, filename, submatrix):
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    return self._do_gen_matrix("dependence probability", X_L_list, X_D_list, M_c, tablename, filename, col=col, confidence=confidence, limit=limit, submatrix=submatrix)

  def gen_feature_z(self, tablename, filename=None,
                    dir=S.path.web_resources_dir):
    if filename is None:
      filename = tablename + '_feature_z'
    full_filename = os.path.join(dir, filename)
    X_L_list, X_D_list, M_c = self.persistence_layer.get_latent_states(tablename)
    return self._do_gen_feature_z(X_L_list, X_D_list, M_c,
                             tablename, full_filename)

  def _analyze_helper(self, tablename, M_c, T, modelid, iterations):
    """Only for one model."""
    X_L_prime, X_D_prime, prev_iterations = self.persistence_layer.get_model(tablename, modelid)

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

    self.persistence_layer.add_samples_for_model(tablename, X_L_prime, X_D_prime, prev_iterations + iterations, modelid)
    return (prev_iterations + iterations)

  def _dependence_probability(self, col1, col2, X_L_list, X_D_list, M_c, T):
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

  def _view_similarity(self, col1, col2, X_L_list, X_D_list, M_c, T):
    prob_dep = 0
    for X_L in X_L_list:
      assignments = X_L['column_partition']['assignments']
      if assignments[col1] == assignments[col2]:
        prob_dep += 1
    prob_dep /= float(len(X_L_list))
    return prob_dep

  def _mutual_information(self, col1, col2, X_L_list, X_D_list, M_c, T):
    t = time.time()
    Q = [(col1, col2)]
    ## Returns list of lists.
    ## First list: same length as Q, so we just take first.
    ## Second list: MI, linfoot. we take MI.
    results_by_model = self.backend.mutual_information(M_c, X_L_list, X_D_list, Q)[0][0]
    ## Report the average mutual information over each model.
    mi = float(sum(results_by_model)) / len(results_by_model)
    print time.time() - t
    return mi

  def _correlation(self, col1, col2, X_L_list, X_D_list, M_c, T):
    t_array = numpy.array(T, dtype=float)
    correlation, p_value = pearsonr(t_array[:,col1], t_array[:,col2])
    return correlation

  def _do_gen_matrix(self, col_function_name, X_L_list, X_D_list, M_c, T, tablename='', filename=None, col=None, confidence=None, limit=None, submatrix=False):
      if col_function_name == 'mutual information':
        col_function = getattr(self, '_mutual_information')
      elif col_function_name == 'dependence probability':
        col_function = getattr(self, '_dependence_probability')
      elif col_function_name == 'correlation':
        col_function = getattr(self, '_correlation')
      elif col_function_name == 'view_similarity':
        col_function = getattr(self, '_view_similarity')
      else:
        raise Exception('Invalid column function')

      num_cols = len(X_L_list[0]['column_partition']['assignments'])
      column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
      column_names = numpy.array(column_names)
      # extract unordered z_matrix
      num_latent_states = len(X_L_list)
      z_matrix = numpy.zeros((num_cols, num_cols))
      for i in range(num_cols):
        for j in range(num_cols):
          z_matrix[i][j] = col_function(i, j, X_L_list, X_D_list, M_c, T)

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

      title = 'Pairwise column %s for %s' % (col_function_name, tablename)
      if filename:
        utils.plot_matrix(z_matrix_reordered, column_names_reordered, title, filename)

      return dict(
        matrix=z_matrix_reordered,
        column_names=column_names_reordered,
        title=title,
        filename=filename,
        message = "Created " + title
        )

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

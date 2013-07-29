#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
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
#
import pylab
import numpy
import psycopg2
import matplotlib.cm
#
import tabular_predDB.python_utils.api_utils as au
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.settings as S

# For testing
from tabular_predDB.LocalEngine import LocalEngine as Engine
engine = Engine()

dbname = 'sgeadmin'
user = os.environ['USER']
psycopg_connect_str = 'dbname=%s user=%s' % (dbname, user)

class MiddlewareEngine(object):

  def __init__(self, backend_hostname='localhost', backend_uri=8007):
    self.backend_hostname = backend_hostname
    self.BACKEND_URI = 'http://' + backend_hostname + ':' + str(backend_uri)

  def ping(self):
    return "MIDDLEWARE GOT PING"

  def runsql(self, sql_command, order_by=False):
    """Run an arbitrary sql command. Returns the query results for select; 0 if not select."""
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute(sql_command)
      try:
        data = cur.fetchall()
        col_metadata = cur.description
        colnames = [coltuple[0] for coltuple in col_metadata]
        ret = {'data':data, 'columns':colnames}
      except psycopg2.ProgrammingError:
        ret = 0
      if order_by:
        # GET X_L AND X_D
        tablename = re.search(r'from\s+(?P<tablename>[^\s]+)', sql_command).group('tablename').strip()
        X_L_list, X_D_list, M_c = self.get_latent_states(tablename)
        ret = self.order_by_similarity(colnames, ret, X_L_list, X_D_list, M_c, order_by)
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)      
      return e
    finally:
      conn.close()
    return ret


  def start_from_scratch(self):
    # drop
    cmd_str = 'dropdb -U %s %s' % (user, dbname)
    os.system(cmd_str)
    # create
    cmd_str = 'createdb -U %s %s' % (user, dbname)
    os.system(cmd_str)
    #
    script_filename = os.path.join(S.path.this_repo_dir,
                                   'install_scripts/table_setup.sql')
    cmd_str = 'psql %s %s -f %s' % (dbname, user, script_filename)
    os.system(cmd_str)
    return 'STARTED FROM SCRATCH'

  def drop_and_load_db(self, filename):
    if not os.path.isfile(filename):
      raise_str = 'drop_and_load_db(%s): filename does not exist' % filename
      raise Exception(raise_str)
    # drop
    cmd_str = 'dropdb %s' % dbname
    os.system(cmd_str)
    # create
    cmd_str = 'createdb %s' % dbname
    os.system(cmd_str)
    # load
    if filename.endswith('.gz'):
      cmd_str = 'gunzip -c %s | psql %s %s' % (filename, dbname, user)
    else:
      cmd_str = 'psql %s %s < %s' % (dbname, user, filename)
    os.system(cmd_str)

  def drop_tablename(self, tablename):
    """Delete table by tablename."""
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute('DROP TABLE %s' % tablename)
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableids = cur.fetchall()
      for tid in tableids:
        tableid = tid[0]
        cur.execute("DELETE FROM preddb.models WHERE tableid=%d;" % tableid)
        cur.execute("DELETE FROM preddb.table_index WHERE tableid=%d;" % tableid)
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)      
      return e
    finally:
      conn.close()
    return 0

  def delete_chain(self, tablename, chain_index):
     """Delete one chain."""
     try:
       conn = psycopg2.connect(psycopg_connect_str)
       cur = conn.cursor()
       cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename)
       tableids = cur.fetchall()
       for tid in tableids:
         tableid = tid[0]
         cur.execute("DELETE FROM preddb.models WHERE tableid=%d;" % tableid)
         cur.execute("DELETE FROM preddb.table_index WHERE tableid=%d;" % tableid)
       conn.commit()
     except psycopg2.DatabaseError, e:
       print('Error %s' % e)      
       return e
     finally:
       conn.close()
     return 0

  def update_datatypes(self, tablename, mappings):
    """
    mappings is a dict of column name to 'continuous', 'multinomial',
    or an int, which signifies multinomial of a specific type.
    TODO: FIX HACKS. Current works by reloading all the data from csv,
    and you it ignores multinomials of specific types.
    Also, disastrous things may happen if you update a schema after creating models.
    """
    # First, get existing cctypes, and T, M_c, and M_r.
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % (tablename))
      tableid = cur.fetchone()[0]
      cur.execute("SELECT MAX(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
      max_chainid = cur.fetchone()[0]
      cur.execute("SELECT cctypes, t, m_r, m_c, path FROM preddb.table_index WHERE tablename='%s';" % tablename)
      cctypes_json, t_json, m_r_json, m_c_json, csv_abs_path = cur.fetchone()
      cctypes = json.loads(cctypes_json)
      t = json.loads(t_json)
      m_r = json.loads(m_r_json)
      m_c = json.loads(m_c_json)
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return 'Caught DB Error: ' + str(e)
    finally:
      conn.close()
    if max_chainid is not None:
      return 'Error: cannot update datatypes after models have already been created. Please create a new table.'

    # Now, update cctypes, T, M_c, and M_r
    for col, mapping in mappings.items():
      ## TODO: fix this hack! See method's docstring.
      if type(mapping) == int:
        mapping = 'multinomial'
      cctypes[m_c['name_to_idx'][col]] = mapping
    t, m_r, m_c, header = du.read_data_objects(csv_abs_path, cctypes=cctypes)

    # Now, put cctypes, T, M_c, and M_r back into the DB
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("UPDATE preddb.table_index SET cctypes='%s', m_r='%s', m_c='%s', t='%s' WHERE tablename='%s';" % (json.dumps(cctypes), json.dumps(m_r), json.dumps(m_c), json.dumps(t), tablename))
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return 'Caught DB Error: ' + str(e)
    finally:
      conn.close()
    colnames = [m_c['idx_to_name'][str(idx)] for idx in range(len(m_c['idx_to_name']))]
    return dict(columns=colnames, data=[cctypes])
      
  def upload_data_table(self, tablename, csv, crosscat_column_types):
    """Upload a csv table to the predictive db.
    Crosscat_column_types must be a dictionary mapping column names
    to either 'ignore', 'continuous', or 'multinomial'. Not every
    column name must be present in the dictionary: default is continuous."""
    # First, test if table with this name already exists, and fail if it does
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("select exists(select * from information_schema.tables where table_name='%s');" % tablename)
      if cur.fetchone()[0]:
        return "Error: table with that name already exists."
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return 'Caught DB Error: ' + str(e)
    finally:
      conn.close()

    # Write csv to file
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    f = open('%s/../../www/data/%s.csv' % (cur_dir, tablename), 'w')
    csv_abs_path = os.path.abspath(f.name)
    f.write(csv)
    f.close()
    os.chmod(csv_abs_path, 0755)
    
    # Write csv to a file, with colnames (first row) removed
    clean_csv = csv[csv.index('\n')+1:]
    f = open('%s/../../www/data/%s_clean.csv' % (cur_dir, tablename), 'w')
    clean_csv_abs_path = os.path.abspath(f.name)
    f.write(clean_csv)
    f.close()
    os.chmod(clean_csv_abs_path, 0755)
    
    # Parse column names to create table
    csv = csv.replace('\r', '')
    colnames = csv.split('\n')[0].split(',')
    
    # Guess the schema. Complete the given crosscat_column_types, which may have missing data, into cctypes
    # Also make the corresponding postgres column types.
    postgres_coltypes = []
    cctypes = []
    header, values = du.read_csv(csv_abs_path, has_header=True)
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
        
    # TODO: warning: m_r and m_c have 0-indexed indices
    #       but the db has 1-indexed keys
    t, m_r, m_c, header = du.read_data_objects(csv_abs_path, cctypes=cctypes)
    colstring = ', '.join([
        ' '.join(tup)
        for tup in zip(colnames, postgres_coltypes)
        ])
    # Execute queries
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("CREATE TABLE %s (%s);" % (tablename, colstring))
      with open(clean_csv_abs_path) as fh:
        cur.copy_from(fh, '%s' % tablename, sep=',')
      curtime = datetime.datetime.now().ctime()
      cur.execute("INSERT INTO preddb.table_index (tablename, numsamples, uploadtime, analyzetime, t, m_r, m_c, cctypes, path) VALUES ('%s', %d, '%s', NULL, '%s', '%s', '%s', '%s', '%s');" % (tablename, 0, curtime, json.dumps(t), json.dumps(m_r), json.dumps(m_c), json.dumps(cctypes), csv_abs_path))
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return 'Caught DB Error: ' + str(e)
    finally:
      if conn:
        conn.close()    
    return dict(columns=colnames, data=[cctypes])

  def import_samples(self, tablename, X_L_list, X_D_list, M_c, T, iterations=0):
    """Import these samples as if they are new chains"""
    # Get t, m_c, and m_r, and tableid
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT t, m_r, m_c FROM preddb.table_index WHERE tablename='%s';" % tablename)
      t_json, m_r_json, m_c_json = cur.fetchone()
      t = json.loads(t_json)
      m_r = json.loads(m_r_json)
      m_c = json.loads(m_c_json)
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % (tablename))
      tableid = cur.fetchone()[0]
      cur.execute("SELECT MAX(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
      max_chainid = cur.fetchone()[0]
      if max_chainid is None: max_chainid = -1
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    except psycopg2.ProgrammingError:
      conn.commit()
    finally:
      if conn:
        conn.close()

    # Insert states for each chain into the middleware db
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      curtime = datetime.datetime.now().ctime()
      ## TODO: This is dangerous. We're using the new M_c, but cctypes will be out of date. Need to update cctypes.
      cur.execute("UPDATE preddb.table_index SET m_c='%s', t='%s' WHERE tablename='%s';" % (json.dumps(M_c), json.dumps(T), tablename))
      for idx, (X_L, X_D) in enumerate(zip(X_L_list, X_D_list)):
        chain_index = max_chainid + 1 + idx
        cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime, chainid, iterations) VALUES (%d, '%s', '%s', '%s', %d, %d);" % (tableid, json.dumps(X_L), json.dumps(X_D), curtime, chain_index, iterations))        
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
    return 0
    
  def create_model(self, tablename, n_chains):
    """Call initialize n_chains times."""
    # Get t, m_c, and m_r, and tableid
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT t, m_r, m_c FROM preddb.table_index WHERE tablename='%s';" % tablename)
      t_json, m_r_json, m_c_json = cur.fetchone()
      t = json.loads(t_json)
      m_r = json.loads(m_r_json)
      m_c = json.loads(m_c_json)
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % (tablename))
      tableid = cur.fetchone()[0]
      cur.execute("SELECT MAX(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
      max_chainid = cur.fetchone()[0]
      if max_chainid is None: max_chainid = 0
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    except psycopg2.ProgrammingError:
      conn.commit()
    finally:
      if conn:
        conn.close()

    # Call initialize on backend
    states_by_chain = list()
    args_dict = dict()
    args_dict['M_c'] = m_c
    args_dict['M_r'] = m_r
    args_dict['T'] = t
    for chain_index in range(max_chainid, n_chains + max_chainid):
      out, id = au.call('initialize', args_dict, self.BACKEND_URI)
      x_l_prime, x_d_prime = out
      states_by_chain.append((x_l_prime, x_d_prime))
    
    # Insert initial states for each chain into the middleware db
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      curtime = datetime.datetime.now().ctime()
      for chain_index in range(n_chains):
        cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime, chainid, iterations) VALUES (%d, '%s', '%s', '%s', %d, 0);" % (tableid, json.dumps(x_l_prime), json.dumps(x_d_prime), curtime, chain_index))        
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
    return 0

  def analyze(self, tablename, chain_index=1, iterations=2, wait=False):
    """Run analyze for the selected table. chain_index may be 'all'."""
    # Get M_c, T, X_L, and X_D from database
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid = int(cur.fetchone()[0])
      cur.execute("SELECT m_c, t FROM preddb.table_index WHERE tableid=%d;" % tableid)
      M_c_json, T_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      T = json.loads(T_json)
      if (str(chain_index).upper() == 'ALL'):
        cur.execute("SELECT DISTINCT(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
        chainids = [my_tuple[0] for my_tuple in cur.fetchall()]
        chainids = map(int, chainids)
        print('chainids: %s' % chainids)
      else:
        chainids = [chain_index]
      conn.commit()
      p_list = []
      for chainid in chainids:
        analyze_helper(tableid, M_c, T, chainid, iterations, self.BACKEND_URI)
      #   from multiprocessing import Process
      #   p = Process(target=analyze_helper,
      #               args=(tableid, M_c, T, chainid, iterations, self.BACKEND_URI))
      #   p_list.append(p)
      #   p.start()
      # if wait:
      #   for p in p_list:
      #     p.join()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
    return 0

  def infer(self, tablename, columnstring, newtablename, confidence, whereclause, limit, numsamples, order_by=False):
    """Impute missing values.
    Sample INFER: INFER columnstring FROM tablename WHERE whereclause WITH confidence LIMIT limit;
    Sample INFER INTO: INFER columnstring FROM tablename WHERE whereclause WITH confidence INTO newtablename LIMIT limit;
    Argument newtablename == null/emptystring if we don't want to do INTO
    """
    # TODO: actually read newtablename.
    # TODO: actually impute only missing values, instead of all values.
    # Get M_c, X_L, and X_D from database
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT tableid, m_c, t FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid, M_c_json, t_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      t = json.loads(t_json)
      cur.execute("SELECT COUNT(*) FROM %s;" % tablename)
      numrows = cur.fetchone()[0]
      cur.execute("SELECT DISTINCT(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
      chainids = [my_tuple[0] for my_tuple in cur.fetchall()]
      chainids = map(int, chainids)
      X_L_list = list()
      X_D_list = list()
      for chainid in chainids:
        cur.execute("SELECT x_l, x_d FROM preddb.models WHERE tableid=%d AND chainid=%d AND " % (tableid, chainid)
                  + "iterations=(SELECT MAX(iterations) FROM preddb.models WHERE tableid=%d AND chainid=%d);" % (tableid, chainid))
        X_L_prime_json, X_D_prime_json = cur.fetchone()
        X_L_list.append(json.loads(X_L_prime_json))
        X_D_list.append(json.loads(X_D_prime_json))
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()

    t_array = numpy.array(t, dtype=float)
    name_to_idx = M_c['name_to_idx']
    colnames = [colname.strip() for colname in columnstring.split(',')]
    col_indices = [name_to_idx[colname] for colname in colnames]
    Q = []
    for row_idx in range(numrows):
      for col_idx in col_indices:
        if numpy.isnan(t_array[row_idx, col_idx]):
          Q.append([row_idx, col_idx])

    # FIXME: the purpose of the whereclause is to specify 'given'
    #        p(missing_value | X_L, X_D, whereclause)
    if whereclause=="" or '=' not in whereclause:
      Y = None
    else:
      varlist = [[c.strip() for c in b.split('=')] for b in whereclause.split('AND')]
      Y = [(numrows+1, name_to_idx[colname], colval) for colname, colval in varlist]
      # map values to codes
      Y = [(r, c, du.convert_value_to_code(M_c, c, colval)) for r,c,colval in Y]

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
      #out, id = au.call('impute_and_confidence', args_dict, self.BACKEND_URI)
      # TODO: call with whole X_L_list and X_D_list once multistate impute implemented
      out = engine.impute_and_confidence(M_c, X_L_list, X_D_list, Y, [q], numsamples)
      value, conf = out
      if conf >= confidence:
        row_idx = q[0]
        col_idx = q[1]
        ret.append((row_idx, col_idx, value))
        counter += 1
        if counter >= limit:
          break
    #ret = du.map_from_T_with_M_c(ret, M_c)
    imputations_list = [(r, c, du.convert_code_to_value(M_c, c, code)) for r,c,code in ret]
    ## Convert into dict with r,c keys
    imputations_dict = dict()
    for r,c,val in imputations_list:
      imputations_dict[(r,c)] = val
    ret = self.select(tablename, columnstring, whereclause, limit, order_by=False, imputations_dict=imputations_dict)
    ret['data'] = self.order_by_similarity(ret['columns'], ret['data'], X_L_list, X_D_list, M_c, order_by)
    return ret

  def select(self, tablename, columnstring, whereclause, limit, order_by, imputations_dict=None):
    probability_query = False
    data_query = False
    M_c, M_r, T = self.get_metadata_and_table(tablename)
    conds = list() ## List of (c_idx, op, val) tuples.
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
        val = int(vals[1].strip())
        c_idx = M_c['name_to_idx'][column]
        conds.append((c_idx, op, val))

    ## queries is a list of c_idxs or (c_idx, value) tuples. A tuple indicates that it's a probability query.
    if '*' in columnstring:
      colnames = []
      queries = []
      data_query = True
      for idx in range(len(M_c['name_to_idx'].keys())):
        queries.append(idx)
        colnames.append(M_c['idx_to_name'][str(idx)])
    else:
      colnames = [colname.strip() for colname in columnstring.split(',')]
      queries = []
      for idx, colname in enumerate(colnames):
        p_match = re.search(r'probability\s*\(\s*(?P<column>[^\s]+)\s*=\s*(?P<value>[^\s]+)\s*\)', colname.lower())
        if p_match:
          column = p_match.group('column')
          c_idx = M_c['name_to_idx'][column]
          value = int(p_match.group('value'))
          queries.append((c_idx, value))
          probability_query = True
        else:
          queries.append(M_c['name_to_idx'][colname])
          data_query = True
    colnames = ['row_id'] + colnames
    queries = ['row_id'] + queries

    ## Helper function that applies WHERE conditions to row.
    def is_row_valid(idx, row):
      for (c_idx, op, val) in conds:
        if not op(row[c_idx], val):
          return False
      if imputations_dict:
        has_imputation = False
        for q in queries:
          if (idx, q) in imputations_dict:
            has_imputation = True
        return has_imputation
      return True

    if probability_query:
      X_L_list, X_D_list, M_c = self.get_latent_states(tablename)

      if whereclause=="" or '=' not in whereclause:
        Y = None
      else:
        varlist = [[c.strip() for c in b.split('=')] for b in whereclause.split('AND')]
        Y = [(numrows+1, name_to_idx[colname], colval) for colname, colval in varlist]
        # map values to codes
        Y = [(r, c, du.convert_value_to_code(M_c, c, colval)) for r,c,colval in Y]
        
    def convert_row(row):
      row = []
      for cidx, code in enumerate(row): #tuple([du.convert_code_to_value(M_c, cidx, code) for cidx, code in enumerate(row)])
        if not numpy.isnan(code) and not code=='nan':
          row.append(du.convert_code_to_value(M_c, cidx, code))
        else:
          row.append(code)
      return tuple(row)
    
    ## Do the select
    data = []
    row_count = 0
    probabilities_only = True
    for idx, row in enumerate(T):
      ## Convert row to values
      #row = convert_row(row)
      if is_row_valid(idx, row): ## Where clause filtering.
        ## Now: get the desired elements.
        ret_row = []
        for q in queries:
          if type(q) == str and q=='row_id':
            ret_row.append(idx)
            probabilities_only = False
          elif type(q) == int:
            if imputations_dict and (idx,q) in imputations_dict:
              val = imputations_dict[(idx,q)]
            else:
              val = row[q]
            ret_row.append(val)
            probabilities_only = False
          elif type(q) == tuple:
            (c_idx, value) = q
            val = float(M_c['column_metadata'][c_idx]['code_to_value'][str(value)])
            Q = [(idx, c_idx, val)]
            prob = engine.simple_predictive_probability(M_c, X_L_list[0], X_D_list[0], Y, Q)
            ## TODO: SELECT PROBABILITY. Need to hook up simple_predictive_sample: for another time.
            ret_row.append(prob)
        data.append(tuple(ret_row))
        row_count += 1
        if (row_count >= limit and not order_by) or probabilities_only:
          break

    ## Prepare for return
    ret = {'data': data, 'columns': colnames}
    if order_by:
      X_L_list, X_D_list, M_c = self.get_latent_states(tablename)
      ret['data'] = self.order_by_similarity(colnames, ret['data'], X_L_list, X_D_list, M_c, order_by)
      if limit and limit != float("inf"):
        ret['data'] = ret['data'][:limit]
    return ret

  def order_by_similarity(self, colnames, data_tuples, X_L_list, X_D_list, M_c, order_by):
    # Return the original data tuples, but sorted by similarity to the given row_id
    # By default, average the similarity over columns, unless one particular column id is specified.
    # TODO
    if len(data_tuples) == 0 or not order_by:
      return data_tuples
    target_rowid = order_by['rowid']
    target_column = order_by['column']
    if target_column:
      col_idxs = [M_c['name_to_idx'][target_column]]
    else:
      col_idxs = range(len(data_tuples[0])-1)
    
    scored_data_tuples = list() ## Entries are (score, data_tuple)
    for idx, data_tuple in enumerate(data_tuples):
      score = 0
      ## Assume row is first value in returned data.
      rowid = data_tuple[0]
      for X_L, X_D in zip(X_L_list, X_D_list):
        for col_idx in col_idxs:
          view_idx = X_L['column_partition']['assignments'][col_idx]
          if X_D[view_idx][rowid] == X_D[view_idx][target_rowid]:
            score += 1
      scored_data_tuples.append((score, data_tuple))
    scored_data_tuples.sort(key=lambda tup: tup[0], reverse=True)
    #print [tup[0] for tup in scored_data_tuples] # print similarities
    return [tup[1] for tup in scored_data_tuples]


  def predict(self, tablename, columnstring, newtablename, whereclause, numpredictions):
    """Simple predictive samples. Returns one row per prediction, with all the given and predicted variables."""
    # TODO: Actually read newtablename.
    # Get M_c, X_L, and X_D from database
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT tableid, m_c, t FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid, M_c_json, t_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      t = json.loads(t_json)
      cur.execute("SELECT COUNT(*) FROM %s;" % tablename)
      numrows = int(cur.fetchone()[0])
      cur.execute("SELECT DISTINCT(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
      chainids = [my_tuple[0] for my_tuple in cur.fetchall()]
      chainids = map(int, chainids)
      X_L_list = list()
      X_D_list = list()
      for chainid in chainids:
        cur.execute("SELECT x_l, x_d FROM preddb.models WHERE tableid=%d AND chainid=%d AND " % (tableid, chainid)
                  + "iterations=(SELECT MAX(iterations) FROM preddb.models WHERE tableid=%d AND chainid=%d);" % (tableid, chainid))
        X_L_prime_json, X_D_prime_json = cur.fetchone()
        X_L_list.append(json.loads(X_L_prime_json))
        X_D_list.append(json.loads(X_D_prime_json))
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Database Error: %s' % e)
      return e
    finally:
      if conn:
        conn.close()

    name_to_idx = M_c['name_to_idx']
    colnames = [colname.strip() for colname in columnstring.split(',')]
    col_indices = [name_to_idx[colname] for colname in colnames]
    Q = [(numrows+1, col_idx) for col_idx in col_indices]
    # parse whereclause
    if whereclause=="" or '=' not in whereclause:
      Y = None
    else:
      varlist = [[c.strip() for c in b.split('=')] for b in whereclause.split('AND')]
      Y = [(numrows+1, name_to_idx[colname], colval) for colname, colval in varlist]
      # map values to codes
      Y = [(r, c, du.convert_value_to_code(M_c, c, colval)) for r,c,colval in Y]

    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['X_L'] = X_L_list
    args_dict['X_D'] = X_D_list
    args_dict['Y'] = Y
    args_dict['Q'] = Q
    args_dict['n'] = numpredictions
    out, id = au.call('simple_predictive_sample', args_dict, self.BACKEND_URI)

    """
    # convert to coordinate format so it can be mapped to original codes
    # output is [[row1,col1,value1],[row2,col2,value2],...]
    new_out = []
    new_row_indices = range(numrows, numrows + numpredictions)
    for new_row_idx, row_values in zip(new_row_indices, out):
      for col_idx, cell_value in zip(col_indices, row_values):
        new_row = [new_row_idx, col_idx, cell_value]
        new_out.append(new_row)
    new_out = du.map_from_T_with_M_c(new_out, M_c)
    """

    # convert to data, columns dict output format
    columns = colnames
    # map codes to original values
    ## TODO: Add histogram call back in, but on Python client locally!
    #self.create_histogram(M_c, numpy.array(out), columns, col_indices, tablename+'_histogram')
    data = [[du.convert_code_to_value(M_c, cidx, code) for cidx,code in zip(col_indices,vals)] for vals in out]
    #data = numpy.array(out, dtype=float).reshape((numpredictions, len(colnames)))
    # FIXME: REMOVE WHEN DONE DEMO
    #data = numpy.round(data, 1)
    ret = {'columns': columns, 'data': data}
    return ret

  def write_json_for_table(self, tablename):
    M_c, M_r, t_dict = self.get_metadata_and_table(tablename)
    X_L_list, X_D_list, M_c = self.get_latent_states(tablename)
    write_json_for_table(t_dict, M_c, X_L_list, X_D_list, M_r)

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

  def get_metadata_and_table(self, tablename):
    """Return M_c and M_r and T"""
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT m_c, m_r, t FROM preddb.table_index WHERE tablename='%s';" % tablename)
      M_c_json, M_r_json, t_json = cur.fetchone()
      conn.commit()
      M_c = json.loads(M_c_json)
      M_r = json.loads(M_r_json)
      t = json.loads(t_json)
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
    # # map T to json object
    # table = []
    # for row_idx, row in enumerate(t):
    #   for col_idx, value in enumerate(row):
    #     row_name = M_r['idx_to_name'][str(row_idx)]
    #     col_name = M_c['idx_to_name'][str(col_idx)]
    #     element = dict(i=row_idx, j=col_idx, value=int(value!=0), row=row_name, col=col_name)
    #     table.append(element)
    # # t_dict = dict(table=table)
    return M_c, M_r, t

  def get_latent_states(self, tablename):
    """Return x_l_list and x_d_list"""
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT tableid, m_c FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid, M_c_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      cur.execute("SELECT DISTINCT(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
      chainids = [my_tuple[0] for my_tuple in cur.fetchall()]
      chainids = map(int, chainids)
      X_L_list = list()
      X_D_list = list()
      for chainid in chainids:
        cur.execute("SELECT x_l, x_d FROM preddb.models WHERE tableid=%d AND chainid=%d AND " % (tableid, chainid)
                  + "iterations=(SELECT MAX(iterations) FROM preddb.models WHERE tableid=%d AND chainid=%d);" % (tableid, chainid))
        X_L_prime_json, X_D_prime_json = cur.fetchone()
        X_L_list.append(json.loads(X_L_prime_json))
        X_D_list.append(json.loads(X_D_prime_json))
  #      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
    return (X_L_list, X_D_list, M_c)

  def estimate_dependence_probabilities(self, tablename, col, confidence, limit, filename):
    X_L_list, X_D_list, M_c = self.get_latent_states(tablename)
    return do_gen_feature_z(X_L_list, X_D_list, M_c, tablename, filename, col, confidence, limit)

  def gen_feature_z(self, tablename, filename=None,
                    dir=S.path.web_resources_dir):
    if filename is None:
      filename = tablename + '_feature_z'
    full_filename = os.path.join(dir, filename)
    X_L_list, X_D_list, M_c = self.get_latent_states(tablename)
    return do_gen_feature_z(X_L_list, X_D_list, M_c,
                            tablename, full_filename)

  def dump_db(self, filename, dir=S.path.web_resources_dir):
    full_filename = os.path.join(dir, filename)
    if filename.endswith('.gz'):
      cmd_str = 'pg_dump %s | gzip > %s' % (dbname, full_filename)
    else:
      cmd_str = 'pg_dump %s > %s' % (dbname, full_filename)
    os.system(cmd_str)
    return 0

  def guessschema(self, tablename, csv):
    """Guess crosscat types. Returns a list indicating each columns type: 'ignore',
    'continuous', or 'multinomial'."""
    try:
      conn = psycopg2.connect(psycopg_connect_str)
      cur = conn.cursor()
      cur.execute("SELECT cctypes FROM preddb.table_index WHERE tablename='%s';" % tablename)
      cctypes = cur.fetchone()[0]
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
    return json.loads(cctypes)

# helper functions
get_name = lambda x: getattr(x, '__name__')
get_Middleware_Engine_attr = lambda x: getattr(MiddlewareEngine, x)
is_Middleware_Engine_method_name = lambda x: inspect.ismethod(get_Middleware_Engine_attr(x))
#
def get_method_names():
    return filter(is_Middleware_Engine_method_name, dir(MiddlewareEngine))
#
def get_method_name_to_args():
    method_names = get_method_names()
    method_name_to_args = dict()
    for method_name in method_names:
        method = MiddlewareEngine.__dict__[method_name]
        arg_str_list = inspect.getargspec(method).args[1:]
        method_name_to_args[method_name] = arg_str_list
    return method_name_to_args

def analyze_helper(tableid, M_c, T, chainid, iterations, BACKEND_URI):
  """Only for one chain."""
  try:
    conn = psycopg2.connect(psycopg_connect_str)
    cur = conn.cursor()
    exec_str = ("SELECT x_l, x_d, iterations FROM preddb.models"
                + " WHERE tableid=%d AND chainid=%d" % (tableid, chainid)
                + " AND iterations=("
                + " SELECT MAX(iterations) FROM preddb.models WHERE tableid=%d AND chainid=%d" % (tableid, chainid)
                + ");" )
    cur.execute(exec_str)
      
    X_L_prime_json, X_D_prime_json, prev_iterations = cur.fetchone()
    X_L_prime = json.loads(X_L_prime_json)
    X_D_prime = json.loads(X_D_prime_json)
    conn.commit()
  except psycopg2.DatabaseError, e:
    print('psycopg2.DatabaseError %s' % e)
    return e
  finally:
    if conn:
      conn.close()

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
#  out, id = au.call('analyze', args_dict, BACKEND_URI)
  out = engine.analyze(M_c, T, X_L_prime, X_D_prime, (), iterations)
  X_L_prime, X_D_prime = out

  # Store X_L_prime, X_D_prime
  try:
    conn = psycopg2.connect(psycopg_connect_str)
    cur = conn.cursor()
    curtime = datetime.datetime.now().ctime()
    cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime, chainid, iterations) " + \
                "VALUES (%d, '%s', '%s', '%s', %d, %d);" % \
                  (tableid, json.dumps(X_L_prime), json.dumps(X_D_prime), curtime, chainid, prev_iterations + iterations))
    conn.commit()
  except psycopg2.DatabaseError, e:
    print('Error %s' % e)
    return e
  finally:
    if conn:
      conn.close()      
  return 0


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
  return 0

def do_gen_feature_z(X_L_list, X_D_list, M_c, tablename='', filename=None, col=None, confidence=None, limit=None):
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
      z_matrix = z_matrix[columns,:][:,columns]
      column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
      column_names = numpy.array(column_names)
      
      z_matrix_reordered = z_matrix
      column_names_reordered = column_names[columns]
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

    if filename:
      # actually create figure
      fig = pylab.figure()
      fig.set_size_inches(16, 12)
      pylab.imshow(z_matrix_reordered, interpolation='none',
                   cmap=matplotlib.cm.gray_r)
      pylab.colorbar()
      if num_cols < 14:
        pylab.gca().set_yticks(range(num_cols))
        pylab.gca().set_yticklabels(column_names_reordered, size='small')
        pylab.gca().set_xticks(range(num_cols))
        pylab.gca().set_xticklabels(column_names_reordered, rotation=90, size='small')
      else:
        pylab.gca().set_yticks(range(num_cols)[::2])
        pylab.gca().set_yticklabels(column_names_reordered[::2], size='small')
        pylab.gca().set_xticks(range(num_cols)[1::2])
        pylab.gca().set_xticklabels(column_names_reordered[1::2],
                                    rotation=90, size='small')
      pylab.title('column dependencies for: %s' % tablename)
      pylab.savefig(filename)
      #
    ret_dict = dict(
      z_matrix_reordered=z_matrix_reordered,
      column_names_reordered=column_names_reordered,
      )
    return ret_dict

def write_json_for_table(t_dict, M_c, X_L_list, X_D_list, M_r=None):
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

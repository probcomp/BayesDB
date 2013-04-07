import inspect
#
import tabular_predDB.cython_code.State as State
import tabular_predDB.python_utils.sample_utils as su

import psycopg2
import numpy
import os
import pickle
import json
import datetime
import pdb

import tabular_predDB.python_utils.api_utils as au
import tabular_predDB.python_utils.data_utils as du

# For testing
from tabular_predDB.jsonrpc_http.Engine import Engine
engine = Engine()

class MiddlewareEngine(object):

  def __init__(self, backend_hostname='localhost', backend_uri=8007):
    self.backend_hostname = backend_hostname
    self.BACKEND_URI = 'http://' + backend_hostname + ':' + str(backend_uri)

  def runsql(self, sql_command):
    """Run an arbitrary sql command. Returns the query results for select; 0 if not select."""
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute(sql_command)
      if sql_command.split()[0].lower() == 'select':
        ret = cur.fetchall()
      else:
        ret = 0
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)      
      return e
    finally:
      conn.close()
    return ret

  def drop_tablename(self, tablename):
    """Delete table by tablename."""
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute('DROP TABLE preddb_data.%s' % tablename)
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
       conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
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

  def upload_data_table(self, tablename, csv, crosscat_column_types):
    """Upload a csv table to the predictive db.
    Crosscat_column_types must be a dictionary mapping column names
    to either 'ignore', 'continuous', or 'multinomial'. Not every
    column name must be present in the dictionary: default is continuous."""
    # First, test if table with this name already exists, and fail if it does
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("select exists(select * from information_schema.tables where table_name='preddb_data.%s');" % tablename)
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
    f = open('%s/../postgres/%s.csv' % (cur_dir, tablename), 'w')
    csv_abs_path = os.path.abspath(f.name)
    f.write(csv)
    f.close()
    os.chmod(csv_abs_path, 0755)
    
    # Write csv to a file, with colnames (first row) removed
    clean_csv = csv[csv.index('\n')+1:]
    f = open('%s/../postgres/%s_clean.csv' % (cur_dir, tablename), 'w')
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
        '"' + tup[0] + '"' + ' ' + tup[1]
        for tup in zip(colnames, postgres_coltypes)
        ])
    # Execute queries
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("CREATE TABLE preddb_data.%s (%s);" % (tablename, colstring))
      with open(clean_csv_abs_path) as fh:
        cur.copy_from(fh, 'preddb_data.%s' % tablename, sep=',')
      curtime = datetime.datetime.now().ctime()
      cur.execute("INSERT INTO preddb.table_index (tablename, numsamples, uploadtime, analyzetime, t, m_r, m_c, cctypes) VALUES ('%s', %d, '%s', NULL, '%s', '%s', '%s', '%s');" % (tablename, 0, curtime, json.dumps(t), json.dumps(m_r), json.dumps(m_c), json.dumps(cctypes)))
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return 'Caught DB Error: ' + str(e)
    finally:
      if conn:
        conn.close()    
    return 0

  def create_model(self, tablename, n_chains):
    """Call initialize n_chains times."""
    # Get t, m_c, and m_r, and tableid
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("SELECT t, m_r, m_c FROM preddb.table_index WHERE tablename='%s';" % tablename)
      t_json, m_r_json, m_c_json = cur.fetchone()
      t = json.loads(t_json)
      m_r = json.loads(m_r_json)
      m_c = json.loads(m_c_json)
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % (tablename))
      tableid = cur.fetchone()[0]
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()

    # Call initialize on backend
    states_by_chain = list()
    args_dict = dict()
    args_dict['M_c'] = m_c
    args_dict['M_r'] = m_r
    args_dict['T'] = t
    for chain_index in range(n_chains):
#      out = engine.initialize(m_c, m_r, t)
      out, id = au.call('initialize', args_dict, self.BACKEND_URI)
      m_c, m_r, x_l_prime, x_d_prime = out
      states_by_chain.append((x_l_prime, x_d_prime))
    
    # Insert initial states for each chain into the middleware db
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
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
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid = int(cur.fetchone()[0])
      cur.execute("SELECT m_c, t FROM preddb.table_index WHERE tableid=%d;" % tableid)
      M_c_json, T_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      T = json.loads(T_json)
      if (chain_index.upper() == 'ALL'):
        cur.execute("SELECT DISTINCT(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
        chainids = [my_tuple[0] for my_tuple in cur.fetchall()]
        chainids = map(int, chainids)
        print('chainids: %s' % chainids)
      else:
        chainids = [chain_index]
      conn.commit()
      p_list = []
      for chainid in chainids:
        from multiprocessing import Process
        p = Process(target=analyze_helper,
                    args=(tableid, M_c, T, chainid, iterations, self.BACKEND_URI))
        p_list.append(p)
        p.start()
      if wait:
        for p in p_list:
          p.join()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
    return 0

  def select(self, querystring):
    """Run a select query, and return the results in csv format, with appropriate header."""
    # TODO: implement
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
    cur = conn.cursor()
    cur.execute(querystring)
    conn.commit()
    conn.close()
    # Convert results into csv so they can be returned...
    return ""
  
  def infer(self, tablename, columnstring, newtablename, confidence, whereclause, limit):
    """Impute missing values.
    Sample INFER: INFER columnstring FROM tablename WHERE whereclause WITH confidence LIMIT limit;
    Sample INFER INTO: INFER columnstring FROM tablename WHERE whereclause WITH confidence INTO newtablename LIMIT limit;
    Argument newtablename == null/emptystring if we don't want to do INTO
    """
    # TODO: implement
    csv = ""
    #cellnumbers: list of row/col pairs [[r,c], [r,c], ...]
    cellnumbers = json.dumps([[0,0]])
    return csv, cellnumbers 

  def predict(self, tablename, columnstring, newtablename, whereclause, numpredictions):
    """Simple predictive samples. Returns one row per prediction, with all the given and predicted variables."""
    # TODO: FIX
    # Get M_c, X_L, and X_D from database
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("SELECT tableid, m_c FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid, M_c_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      cur.execute("SELECT COUNT(*) FROM preddb_data.%s;" % tablename)
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

    name_to_idx = M_c['name_to_idx']
    Q = [(numrows+1, name_to_idx[colname]) for colname in map(str.strip, columnstring.split(','))]
    Y = [(numrows+1, name_to_idx[colname], colval) for colname, colval in whereclause.iteritems()]
    print 'Q',Q
    print 'Y',Y

    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['X_L'] = X_L_list
    args_dict['X_D'] = X_D_list
    args_dict['Y'] = Y
    args_dict['Q'] = Q
    args_dict['n'] = numpredictions
    engine.simple_predictive_sample(M_c, X_L_list, X_D_list, Y, Q, numpredictions)
#    out, id = au.call('simple_predictive_sample', args_dict, self.BACKEND_URI)
    print 'out',out
    csv = out
    return csv

  def get_latent_states(self, tablename):
    """Return x_l_list and x_d_list"""
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid = cur.fetchone()[0]
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
    return (X_L_list, X_D_list)

  def guessschema(self, tablename, csv):
    """Guess crosscat types. Returns a list indicating each columns type: 'ignore',
    'continuous', or 'multinomial'."""
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
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
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
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
  args_dict['kernel_list'] = None
  args_dict['n_steps'] = iterations
  args_dict['c'] = 'c' # Currently ignored by analyze
  args_dict['r'] = 'r' # Currently ignored by analyze
  args_dict['max_iterations'] = 'max_iterations' # Currently ignored by analyze
  args_dict['max_time'] = 'max_time' # Currently ignored by analyze
  out, id = au.call('analyze', args_dict, BACKEND_URI)
  X_L_prime, X_D_prime = out

  # Store X_L_prime, X_D_prime
  try:
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
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

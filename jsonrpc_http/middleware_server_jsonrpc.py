from __future__ import print_function
#
#  Copyright (c) 2011 Edward Langley
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
#
#  Redistributions in binary form must reproduce the above copyright
#  notice, this list of conditions and the following disclaimer in the
#  documentation and/or other materials provided with the distribution.
#
#  Neither the name of the project's author nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#  TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#

from twisted.internet import ssl
import traceback

from twisted.internet import reactor
from twisted.web import server, iweb
from twisted.web.resource import EncodingResourceWrapper

from jsonrpc.server import ServerEvents, JSON_RPC

import os
import pickle
import json
import datetime
import pdb
#
import psycopg2
#
import tabular_predDB.python_utils.api_utils as au
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.jsonrpc_http.Engine as E
from tabular_predDB.jsonrpc_http.Engine import Engine
Engine_methods = E.get_method_names()
engine = Engine()

class ExampleServer(ServerEvents):
  # inherited hooks
  def log(self, responses, txrequest, error):
    print(txrequest.code, end=' ')
    if isinstance(responses, list):
      for response in responses:
        msg = self._get_msg(response)
        print(txrequest, msg)
    else:
      msg = self._get_msg(responses)
      print(txrequest, msg)

  def findmethod(self, method, args=None, kwargs=None):
    if method in self.methods:
      return getattr(engine, method)
    elif method in self.mymethods:
      return getattr(self, method)
    else:
      return None

  # helper methods
  methods = set(Engine_methods)
  mymethods = set(['runsql', 'upload_data_table', 'create_model', 'analyze', 'select', \
                     'infer', 'predict', 'createmodel', 'guessschema','drop_tablename', 'delete_chain'])
  hostname = 'localhost'
  backend_hostname = 'localhost'
  URI = 'http://' + hostname + ':8008'
  BACKEND_URI = 'http://' + backend_hostname + ':8007'
  def _get_msg(self, response):
    print('response', repr(response))
    return ' '.join(str(x) for x in [response.id, response.result or response.error])
  
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
    pass

  def upload(self, tablename, csv, crosscat_column_types):
    """Upload a csv table to the predictive db.
    Crosscat_column_types must be a dictionary mapping column names
    to either 'ignore', 'continuous', or 'multinomial'. Not every
    column name must be present in the dictionary: default is continuous."""
    # First, test if table with this name already exists, and fail if it does
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("select exists(select * from information_schema.tables where table_name='%s');" % tablename)
      if cur.fetchone()[0]:
        return "Error: table with that name already exists."
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
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
    header, values = du.read_csv(clean_csv_abs_path, has_header=True)
    column_data_lookup = dict(zip(header, numpy.array(values).T))
    for colname in colnames:
      if colname in crosscat_column_types:
        cctype = crosscat_column_types[colname]
      else:
        # cctype = 'continuous'
        column_data = column_data_lookup[colname]
        cctype = du.guess_column_type(column_data)
      cctypes.append(cctype)
      if cctype == 'ignore':
        postgres_coltypes.append('varchar(200)')
      elif cctype == 'continuous':
        postgres_coltypes.append('float8')
      elif cctype == 'multinomial':
        postgres_coltypes.append('varchar(200)')
        
    # Read T from file, while using appropriate cctypes, e.g. ignoring "ignore"s
    # TODO: warning: m_r and m_c have 0-indexed indices, but the db has 1-indexed keys
    t, m_r, m_c, header = du.continuous_or_ignore_from_file_with_colnames(csv_abs_path, cctypes)
    colstring = ', '.join([tup[0] + ' ' + tup[1] for tup in zip(colnames, postgres_coltypes)])



    # Execute queries
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("CREATE TABLE %s (%s);" % (tablename, colstring))
      with open(clean_csv_abs_path) as fh:
        cur.copy_from(fh, tablename, sep=',')
      curtime = datetime.datetime.now().ctime()
      cur.execute("INSERT INTO preddb.table_index (tablename, numsamples, uploadtime, analyzetime, t, m_r, m_c, cctypes) VALUES ('%s', %d, '%s', NULL, '%s', '%s', '%s', '%s');" % (tablename, 0, curtime, json.dumps(t), json.dumps(m_r), json.dumps(m_c), json.dumps(cctypes)))
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()    
    return 0

  def create_model(tablename, n_chains):
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
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s' AND uploadtime='%s';" % (tablename, curtime))
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
      out, id = au.call('initialize', args_dict, self.BACKEND_URI)
      m_c, m_r, x_l_prime, x_d_prime = out
      states_by_chain.append((x_l_prime, x_d_prime))
    
    # Insert initial states for each chain into the middleware db
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      for chain_index in range(n_chains):
        cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime, chainid, iterations) VALUES (%d, '%s', '%s', '%s', %d, 0);" % (tableid, json.dumps(x_l_prime), json.dumps(x_d_prime), curtime, chain_index))        
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()


  def analyze(self, tablename, chain_index=1, iterations=2):
    """Run analyze for the selected table. chain_index may be 'all'."""
    # Get M_c, T, X_L, and X_D from database
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid = cur.fetchone()[0]
      cur.execute("SELECT m_c, t FROM preddb.table_index WHERE tableid=%d;" % tableid)
      M_c_json, T_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      T = json.loads(T_json)
      if (chain_index == 'all'):
        cur.execute("SELECT UNIQUE(chainid) FROM preddb.models WHERE tableid=%d;" % tableid)
        chainids = cur.fetchone()
      else:
        chain_ids = [chain_index]
      conn.commit()
      for chainid in chainids:
        self.analyze_helper(tablename, M_c, T, chainid, iterations)
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()
      
  def analyze_helper(self, tablename, M_c, T, chainid, iterations):
    """Only for one chain."""
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("SELECT x_l, x_d, iterations FROM preddb.models WHERE tableid=%d AND chainid=%d" % (tableid, chainid)
                  + "iterations=(SELECT MAX(iterations) FROM preddb.models WHERE tableid=%d);" % (tableid))
      X_L_prime_json, X_D_prime_json, prev_iterations = cur.fetchone()
      X_L_prime = json.loads(X_L_prime_json)
      X_D_prime = json.loads(X_D_prime_json)
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
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
    args_dict['kernel_list'] = 'kernel_list'
    args_dict['n_steps'] = number
    args_dict['c'] = 'c' # Currently ignored by analyze
    args_dict['r'] = 'r' # Currently ignored by analyze
    args_dict['max_iterations'] = 'max_iterations' # Currently ignored by analyze
    args_dict['max_time'] = 'max_time' # Currently ignored by analyze
    out, id = au.call('analyze', args_dict, self.BACKEND_URI)
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
    cellnumbers = []
    return csv, cellnumbers 

  def predict(self, tablename, columnstring, newtablename, whereclause, numpredictions):
    """Simple predictive samples. Returns one row per prediction, with all the given and predicted variables."""
    # TODO: FIX
    # Get M_c, X_L, and X_D from database
    try:
      conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
      cur = conn.cursor()
      cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename)
      tableid = cur.fetchone()[0]
      cur.execute("SELECT m_c FROM preddb.table_index WHERE tableid=%d;" % tableid)
      M_c_json = cur.fetchone()
      M_c = json.loads(M_c_json)
      cur.execute("SELECT x_l, x_d FROM preddb.models WHERE tableid=%d AND " % tableid
                  + "modeltime=(SELECT MAX(modeltime) FROM preddb.models WHERE tableid=%d);" % tableid)
      X_L_prime_json, X_D_prime_json = cur.fetchone()
      X_L_prime = json.loads(X_L_prime_json)
      X_D_prime = json.loads(X_D_prime_json)
      conn.commit()
    except psycopg2.DatabaseError, e:
      print('Error %s' % e)
      return e
    finally:
      if conn:
        conn.close()

    # columnstring is 

    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['X_L'] = X_L_prime
    args_dict['X_D'] = X_D_prime
    args_dict['Y'] = None # Y: given values. TODO: extract from whereclause?
    args_dict['Q'] = [(0,0), (0,1)] # Query row: Q[0][0], cols: [q[1] for q in Q]
    args_dict['n'] = 1
    for idx in range(numpredictions):
      out, id = au.call('simple_predictive_sample', args_dict, self.BACKEND_URI)
    csv = ""
    return csv

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


class CorsEncoderFactory(object):
  
  def encoderForRequest(self, request):
    request.setHeader("Access-Control-Allow-Origin", '*')
    request.setHeader("Access-Control-Allow-Methods", 'PUT, GET')
    return _CorsEncoder(request)

  
class _CorsEncoder(object):
  """
  @ivar _request: A reference to the originating request.
  
  @since: 12.3
  """
    
  def __init__(self, request):
    self._request = request
      
  def encode(self, data):
    print(data)
    return data
      
  def finish(self):
    return ""


root = JSON_RPC().customize(ExampleServer)
wrapped = EncodingResourceWrapper(root, [CorsEncoderFactory()])
site = server.Site(wrapped)

# 8008 is the port you want to run under. Choose something >1024
PORT = 8008
print('Listening on port %d...' % PORT)
reactor.listenTCP(PORT, site)
reactor.run()

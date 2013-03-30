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
from twisted.web import server

from jsonrpc.server import ServerEvents, JSON_RPC

import tabular_predDB.jsonrpc_http.Engine as E
Engine_methods = E.get_method_names()

from tabular_predDB.jsonrpc_http.Engine import Engine
engine = Engine()

import psycopg2
import os
import pickle
import json
import datetime
import tabular_predDB.python_utils.api_utils as au
import tabular_predDB.python_utils.data_utils as du

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
  mymethods = set(['add', 'runsql', 'upload', 'select', 'infer', 'predict', 'createmodel', 'guessschema'])
  hostname = 'localhost'
  backend_hostname = 'localhost'
  URI = 'http://' + hostname + ':8008'
  BACKEND_URI = 'http://' + backend_hostname + ':8007'
  def _get_msg(self, response):
    print('response', repr(response))
    return ' '.join(str(x) for x in [response.id, response.result or response.error])
  
  def runsql(self, sql_command):
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
    cur = conn.cursor()
    cur.execute(sql_command)
    conn.commit()
    conn.close()
    return 0

  def upload(self, tablename, csv, crosscat_column_types):
    # Write csv to file, temporarily (do I have to remove first row? test both ways)
    f = open('../postgres/%s.csv' % tablename, 'w')
    csv_abs_path = os.path.abspath(f.name)
    f.write(csv)
    f.close()
    os.chmod(csv_abs_path, 0755)
    
    # Write csv to a file, with colnames (first row) removed
    clean_csv = csv[csv.index('\n')+1:]
    f = open('../postgres/%s_clean.csv' % tablename, 'w')
    clean_csv_abs_path = os.path.abspath(f.name)
    f.write(clean_csv)
    f.close()
    os.chmod(clean_csv_abs_path, 0755)
    
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
    cur = conn.cursor()
    # Parse column names to create table
    csv = csv.replace('\r', '')
    colnames = csv.split('\n')[0].split(',')
    
    # Complete the given crosscat_column_types, which may have missing data, into cctypes
    postgres_coltypes = []
    cctypes = []
    for colname in colnames:
      if colname in crosscat_column_types:
        cctype = crosscat_column_types[colname]
      else:
        cctype = 'continuous'
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
    cur.execute("CREATE TABLE IF NOT EXISTS %s (%s);" % (tablename, colstring))
    # Load CSV into Postgres
    #print ("COPY %s FROM '%s' WITH DELIMITER AS ',' CSV;" % (tablename, clean_csv_abs_path))
    cur.execute("COPY %s FROM '%s' WITH DELIMITER AS ',' CSV;" % (tablename, clean_csv_abs_path))
    uploadtime = datetime.datetime.now().ctime()
    cur.execute("INSERT INTO preddb.table_index (tablename, numsamples, uploadtime, analyzetime, t, m_r, m_c, cctypes) VALUES ('%s', %d, '%s', NULL, '%s', '%s', '%s', '%s');" % (tablename, 0, uploadtime, json.dumps(t), json.dumps(m_r), json.dumps(m_c), json.dumps(cctypes)))

    # Call initialize on backend
    """
    args_dict = dict()
    args_dict['M_c'] = m_c
    args_dict['M_r'] = m_r
    args_dict['T'] = T
    out, id = au.call('initialize', args_dict, BACKEND_URI)
    m_c, m_r, x_l_prime, x_d_prime = out
    
    cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename='%s' AND uploadtime=%s;" % (tablename, uploadtime))
    tableid = cur.fetchone()
    print 'tableid:',tableid
    modeltime = datetime.datetime.now().strftime()
    cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime) VALUES (%d, '%s', '%s', '%s');" % (tableid, json.dumps(x_l_prime), json.dumps(x_d_prime), modeltime))
    """
    conn.commit()
    conn.close()    
    return 0


  def createmodel(self, tablename, number=10, iterations=2):
    # Call analyze on backend
    # Need to get M_c, M_r, and T!!
    """
    args_dict = dict()
    args_dict['M_c'] = M_c
    args_dict['M_r'] = M_r
    args_dict['T'] = T
    out, id = au.call('initialize', args_dict, URI)
    M_c, M_r, X_L_prime, X_D_prime = out
    """
    # Do I need to save X_L_prime and X_D_prime?
    return 0

  def select(self, querystring):
    # return csv
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
    cur = conn.cursor()
    cur.execute(querystring)
    conn.commit()
    conn.close()
    # Convert results into csv so they can be returned...
    return ""
  
  def infer(self, tablename, columnstring, newtablename, confidence, whereclause, limit):
    # INFER columnstring FROM tablename WHERE whereclause WITH confidence LIMIT limit;
    # INFER columnstring FROM tablename WHERE whereclause WITH confidence INTO newtablename LIMIT limit;
    # newtablename == null/emptystring if we don't want to do INTO
    
    # cellnumbers: list of row/col pairs [[r,c], [r,c], ...]
    csv = ""
    cellnumbers = []
    return csv, cellnumbers 

  def predict(self, tablename, columnstring, newtablename, whereclause, numpredictions):
    # Call simple predictive sample on backend
    # one row per prediction, with all the given and predicted variables
    csv = ""
    return csv

  def guessschema(self, tablename, csv):
    """Guess crosscat types"""
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
    cur = conn.cursor()
    cur.execute("SELECT cctypes FROM preddb.table_index WHERE tablename='%s';" % tablename)
    cctypes = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return json.loads(cctypes)
    

# an attempt to change the header access-control-allow-origin: *
class My_JSON_RPC(JSON_RPC):
  def _ebRender(self, result, request, id, finish=True):
    err = None
    if not isinstance(result, BaseException):
      try: result.raiseException()
      except BaseException, e:
        err = e
        self.eventhandler.log(err, request, error=True)
    else: err = result

    err = self.render_error(err, id)
    self._setresponseCode(err, request)

    request.setHeader("content-type", 'application/json')
    result = jsonrpc.jsonutil.encode(err).encode('utf-8')
    request.setHeader("content-length", len(result))
    request.setHeader("Access-Control-Allow-Origin", '*')
    request.write(result)
    if finish: request.finish()

#root = JSON_RPC().customize(ExampleServer)
root = My_JSON_RPC().customize(ExampleServer)
site = server.Site(root)


# 8008 is the port you want to run under. Choose something >1024
PORT = 8008
print('Listening on port %d...' % PORT)
reactor.listenTCP(PORT, site)
reactor.run()

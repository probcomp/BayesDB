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
  mymethods = set(['add', 'runsql', 'upload', 'start', 'select', 'infer', 'predict'])
  hostname = 'localhost'
  URI = 'http://' + hostname + ':8008'
  def _get_msg(self, response):
    print('response', repr(response))
    return ' '.join(str(x) for x in [response.id, response.result or response.error])

  def add(self, a, b):
    print ('adding %d and %d' % (a, b))
    return a+b+2

  def runsql(self, sql_command):
    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
    cur = conn.cursor()
    cur.execute(sql_command)
    conn.commit()
    conn.close()
    return 0

  """
  def create(self, tablename, columns):
    # dump columns, so that we have it stored for testing with middleware_stub_client
    pickle.dump(columns, open('create_%s_columns.pkl' % tablename, 'w'))
    # parse the columns

    conn = psycopg2.connect('dbname=sgeadmin user=sgeadmin')
    cur = conn.cursor()
    #create_table_querystring = ''
    #cur.execute(create_table_querystring)
    #cur.execute("CREATE TABLE dha (id serial PRIMARY KEY, num integer, data varchar);")
    #cur.execute("INSERT INTO preddb.tableindex (tablename, numsamples, uploadtime) VALUES (%s, %s, %s);" % (tablename, 0, ))
    conn.commit()
    conn.close()
    return 'table created'
  """

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
    #def get_postgres_datatype(crosscat_column_type):
    #  return 'float8'
    
    for colname in colnames:
      pass

    coltypes = ['float8']*len(colnames) #[crosscat_column_types['
    coltypes[0] = 'varchar(100)'
    colstring = ', '.join([tup[0] + ' ' + tup[1] for tup in zip(colnames, coltypes)])
    # TODO: add my own primary key
    print ("CREATE TABLE IF NOT EXISTS %s (%s);" % (tablename, colstring))
    cur.execute("CREATE TABLE IF NOT EXISTS %s (%s);" % (tablename, colstring))

    # Load CSV into Postgres
    print ("COPY %s FROM '%s' WITH DELIMITER AS ',' CSV;" % (tablename, clean_csv_abs_path))
    cur.execute("COPY %s FROM '%s' WITH DELIMITER AS ',' CSV;" % (tablename, clean_csv_abs_path))
    conn.commit()
    conn.close()
    return 0


  def createmodel(self, tablename):
    # Call initialize on backend
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

  def start(self, tablename):
    # Call analyze on backend
    # start inference with some default number of samples
    #return # return 0 if inference started properly, or error message.
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
  
  def infer(self, tablename, columnstring, newtablename, confidence, whereclause):
    # INFER columnstring FROM tablename WHERE whereclause WITH confidence;
    # INFER columnstring FROM tablename WHERE whereclause WITH confidence INTO newtablename;
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

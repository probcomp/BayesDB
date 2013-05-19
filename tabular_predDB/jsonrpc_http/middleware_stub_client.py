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
"""
A python client that simulates the frontend.
"""

import time
import inspect
import psycopg2
import pickle
import os

import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.api_utils as au
from tabular_predDB.jsonrpc_http.MiddlewareEngine import MiddlewareEngine
middleware_engine = MiddlewareEngine()

def run_test(hostname='localhost', middleware_port=8008, online=False):
  URI = 'http://' + hostname + ':%d' % middleware_port
  cur_dir = os.path.dirname(os.path.abspath(__file__))  
  test_tablenames = ['dha_small', 'anneal_small']
  
  for tablename in test_tablenames:
    table_csv = open('%s/../../www/data/%s.csv' % (cur_dir, tablename), 'r').read()
    run_test_with(tablename, table_csv, URI, online)

def call(method_name, args_dict, URI, online):
  if online:
    out, id = au.call(method_name, args_dict, URI)
  else:
    method = getattr(middleware_engine, method_name)
    argnames = inspect.getargspec(method)[0]
    args = [args_dict[argname] for argname in argnames if argname in args_dict]
    out = method(*args)
  return out

def run_test_with(tablename, table_csv, URI, crosscat_column_types="None", online=False):
  call('start_from_scratch', {}, URI, online)

  # test upload_data_table
  print 'uploading data table %s' % tablename
  method_name = 'upload_data_table'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['csv'] = table_csv 
  args_dict['crosscat_column_types'] = crosscat_column_types
  out = call(method_name, args_dict, URI, online)
  assert (out==0 or out=="Error: table with that name already exists.")
  # TODO: Test that table was created
  out = call('runsql', {'sql_command': "SELECT tableid FROM preddb.table_index WHERE tablename='%s'" % tablename}, URI, online)
  time.sleep(1)

  if 'dha' in tablename:
    # test runsql
    method_name = 'runsql'
    args_dict = dict()
    args_dict['sql_command'] = 'CREATE TABLE IF NOT EXISTS bob(id INT PRIMARY KEY, num INT);'
    out = call(method_name, args_dict, URI, online)
    assert out==0
    call('runsql', {'sql_command': 'DROP TABLE bob;'}, URI, online)
    args_dict['sql_command'] = 'SELECT * FROM preddb_data.dha_small;'
    
    out = call(method_name, args_dict, URI, online)
    assert out['columns'] == [u'n_death_ill', u'ttl_mdcr_spnd', u'mdcr_spnd_inp', u'mdcr_spnd_outp', u'mdcr_spnd_ltc']
    assert type(out['data']) == list
    time.sleep(1)

  # test createmodel
  method_name = 'create_model'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['n_chains'] = 3 # default is 10
  print 'creating model with %d chains' % args_dict['n_chains']
  out = call(method_name, args_dict, URI, online)  
  assert out==0
  # Test that one model was created
  out = call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
                 + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s';" % tablename}, URI, online)
  assert(out['data'][0][0] == 3)
  out = call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
                 + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s' AND chainid=1;" % tablename}, URI, online)
  assert(out['data'][0][0] == 1)
  time.sleep(1)

  # test analyze
  method_name = 'analyze'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['chain_index'] = 'all'
  args_dict['wait'] = True # wait for analyze to finish
  args_dict['iterations'] = 2
  print 'running analyze for %d iterations on all chains' % args_dict['iterations']
  out = call(method_name, args_dict, URI, online)
  assert (out==0)
  # Test that inference was started - there should now be two rows of latent states once analyze is finished running.
  out = call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
                 + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s';" % tablename}, URI, online)
  assert(out['data'][0][0] == 6)
  time.sleep(1)

  # test get_latent_states
  (X_L_list, X_D_list, M_c) = call('get_latent_states', dict(tablename=tablename), URI, online)
  import json
  json_states = json.dumps(dict(X_L_list=X_L_list, X_D_list=X_D_list))
  with open('json_states', 'w') as fh:
    fh.write(json_states)
  time.sleep(1)

  # test gen_feature_z
  out = call('gen_feature_z', dict(tablename=tablename), URI, online)

  if 'anneal' in tablename:
    # TODO: test infer
    method_name = 'infer'
    args_dict = dict()
    args_dict['tablename'] = tablename
    args_dict['columnstring'] = "temper_rolling, condition"
    args_dict['newtablename'] = "anneal_predict"
    args_dict['whereclause'] = "steel=A"
    args_dict['confidence'] = 0
    args_dict['limit'] = 8
    args_dict['numsamples'] = 10 # should do 10 or 100
    print 'running infer'
    out = call(method_name, args_dict, URI, online)
    print 'infer out:', out
    # TODO
    # Test that missing values are filled in
    time.sleep(1)

    # TODO: test predict
    method_name = 'predict'
    args_dict = dict()
    args_dict['tablename'] = tablename
    args_dict['columnstring'] = "temper_rolling, condition"
    args_dict['newtablename'] = "anneal_predict"
    args_dict['whereclause'] = "steel=A AND product_type=C"
    args_dict['numpredictions'] = 10
    print 'running predict'
    out = call(method_name, args_dict, URI, online)
    print 'predict out:\n',out
    assert out['columns'] == [u'temper_rolling', u'condition']
    assert len(out['data']) == 10
    assert len(out['data'][0]) == len(out['columns'])    
    time.sleep(1)

  if 'dha' in tablename:
    # TODO: test infer
    method_name = 'infer'
    args_dict = dict()
    args_dict['tablename'] = tablename
    args_dict['columnstring'] = "N_DEATH_ILL, MDCR_SPND_INP"
    args_dict['newtablename'] = ""
    args_dict['whereclause'] = 'MDCR_SPND_LTC=6331'
    args_dict['confidence'] = 0
    args_dict['limit'] = 8
    args_dict['numsamples'] = 10 # should do 10 or 100
    print 'running infer'
    #out = middleware_engine.infer(tablename, "N_DEATH_ILL, MDCR_SPND_INP", "", 0, 'MDCR_SPND_LTC=6331', 8, 10)
    out = call(method_name, args_dict, URI, online)
    # TODO: Test that missing values are filled in
    time.sleep(1)

    # TODO: test predict
    method_name = 'predict'
    args_dict = dict()
    args_dict['tablename'] = tablename
    args_dict['columnstring'] = "N_DEATH_ILL, MDCR_SPND_INP"
    args_dict['newtablename'] = ""
    args_dict['whereclause'] = 'MDCR_SPND_LTC=6331'
    args_dict['numpredictions'] = 10
    print 'running predict'
    out = call(method_name, args_dict, URI, online)
    print out
    assert out['columns'] == [u'N_DEATH_ILL', u'MDCR_SPND_INP']
    assert len(out['data']) == 10
    assert len(out['data'][0]) == len(out['columns'])
    time.sleep(1)

  # test delete_chain
  method_name = 'delete_chain'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['chain_index'] = 0
  print 'deleting chain 0'
  out = call(method_name, args_dict, URI, online)
  assert out==0
  # TODO: Test to make sure there's one less chain
  time.sleep(1)

  # drop tablename
  print 'dropping tablename'
  call('drop_tablename', {'tablename': tablename}, URI, online)

  
if __name__ == '__main__':
    run_test()

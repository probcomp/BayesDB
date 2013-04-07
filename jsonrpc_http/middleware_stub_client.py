"""
A python client that simulates the frontend.
"""

import time

#import tabular_predDB.jsonrpc_http.Engine as E
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.api_utils as au
from tabular_predDB.jsonrpc_http.MiddlewareEngine import MiddlewareEngine
middleware_engine = MiddlewareEngine()

import psycopg2
import pickle
import os

def run_test(hostname='localhost', middleware_port=8008):
  URI = 'http://' + hostname + ':%d' % middleware_port
  cur_dir = os.path.dirname(os.path.abspath(__file__))  
  #test_tablenames = ['dhatest', 'dha_small', 'dha_small_cont']
  test_tablenames = ['dha_small']
  
  for tablename in test_tablenames:
    table_csv = open('%s/../postgres/%s.csv' % (cur_dir, tablename), 'r').read()
    run_test_with(tablename, table_csv, URI)


def run_test_with(tablename, table_csv, URI, crosscat_column_types="None"):
  # drop tablename
  au.call('drop_tablename', {'tablename': tablename}, URI)

  # test runsql
  method_name = 'runsql'
  args_dict = dict()
  args_dict['sql_command'] = 'CREATE TABLE IF NOT EXISTS bob(id INT PRIMARY KEY, num INT);'
  out, id = au.call(method_name, args_dict, URI)
  au.call('runsql', {'sql_command': 'DROP TABLE bob;'}, URI)
  time.sleep(1)

  # test upload_data_table
  method_name = 'upload_data_table'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['csv'] = table_csv 
  args_dict['crosscat_column_types'] = crosscat_column_types
  out, id = au.call(method_name, args_dict, URI)
  print out
  assert (out==0 or out=="Error: table with that name already exists.")
  # TODO: Test that table was created
  out, id = au.call('runsql', {'sql_command': "SELECT tableid FROM preddb.table_index WHERE tablename='%s'" % tablename}, URI)
  time.sleep(1)

  # test createmodel
  method_name = 'create_model'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['n_chains'] = 3 # default is 10
  middleware_engine.create_model(tablename, 3)
#  out, id = au.call(method_name, args_dict, URI)  
#  assert out==0
  # Test that one model was created
  out, id = au.call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
                 + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s';" % tablename}, URI)
  assert(out[0][0] == 3)
  out, id = au.call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
                 + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s' AND chainid=1;" % tablename}, URI)
  assert(out[0][0] == 1)
  time.sleep(1)

  # test analyze
  method_name = 'analyze'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['chain_index'] = 'all'
  out, id = au.call(method_name, args_dict, URI)
  assert (out==0)
  # Test that inference was started - there should now be two rows of latent states once analyze is finished running.
  out, id = au.call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
                 + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s';" % tablename}, URI)
  assert(out[0][0] == 2)
  time.sleep(1)

  # test select
  method_name = 'select'
  args_dict = dict()
  args_dict['querystring'] = 'SELECT * FROM %s;' % tablename
  out, id = au.call(method_name, args_dict, URI)
  csv_results = out
  # TODO
  # Test that correct things were selected
  #assert(csv_results == table_csv)
  time.sleep(1)

  # TODO: test infer
  method_name = 'infer'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['columnstring'] = ""
  args_dict['newtablename'] = ""
  args_dict['whereclause'] = ""
  args_dict['confidence'] = 0
  args_dict['limit'] = ""
  out, id = au.call(method_name, args_dict, URI)
  csv_results, cellnumbers = out
  # TODO
  # Test that missing values are filled in
  time.sleep(1)

  # TODO: test predict
  method_name = 'predict'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['columnstring'] = ""
  args_dict['newtablename'] = ""
  args_dict['whereclause'] = ""
  args_dict['numpredictions'] = 10
  out, id = au.call(method_name, args_dict, URI)
  csv_results = out
  # TODO
  # Test that prediction worked properly
  time.sleep(1)

  # test delete_chain
  method_name = 'delete_chain'
  args_dict = dict()
  args_dict['tablename'] = tablename
  args_dict['chain_index'] = 0
  out, id = au.call(method_name, args_dict, URI)
  assert out==0
  # TODO: Test to make sure there's one less chain
  time.sleep(1)

  # drop tablename
  au.call('drop_tablename', {'tablename': tablename}, URI)

  
if __name__ == '__main__':
    run_test()

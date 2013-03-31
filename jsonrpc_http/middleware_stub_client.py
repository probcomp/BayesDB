"""
A python client that simulates the frontend.
"""

import argparse
import time
#
import tabular_predDB.jsonrpc_http.Engine as E
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.api_utils as au

import psycopg2
import pickle

# parse some arguments
parser = argparse.ArgumentParser()
parser.add_argument('--hostname', default='localhost', type=str)
parser.add_argument('--seed', default=0, type=int)
parser.add_argument('--num_clusters', default=2, type=int)
parser.add_argument('--num_cols', default=8, type=int)
parser.add_argument('--num_rows', default=300, type=int)
parser.add_argument('--num_splits', default=2, type=int)
parser.add_argument('--max_mean', default=10, type=float)
parser.add_argument('--max_std', default=0.1, type=float)
parser.add_argument('--start_id', default=0, type=int)
args = parser.parse_args()
hostname = args.hostname
seed = args.seed
num_clusters = args.num_clusters
num_cols = args.num_cols
num_rows = args.num_rows
num_splits = args.num_splits
max_mean = args.max_mean
max_std = args.max_std
id = args.start_id

# settings
URI = 'http://' + hostname + ':8008'
print 'URI: ', URI

tablename = 'dhatest'
table_csv = open('../postgres/%s.csv' % tablename, 'r').read()
crosscat_column_types = pickle.load(open('dhatest_column_types.pkl', 'r'))

method_name = 'runsql'
args_dict = dict()
args_dict['sql_command'] = 'CREATE TABLE IF NOT EXISTS bob(id INT PRIMARY KEY, num INT);'
out, id = au.call(method_name, args_dict, URI)
# TODO: Test that command was executed
au.call('runsql', {'sql_command': 'DROP TABLE bob;'}, URI)
time.sleep(1)

method_name = 'upload'
args_dict = dict()
args_dict['tablename'] = tablename
args_dict['csv'] = table_csv 
args_dict['crosscat_column_types'] = crosscat_column_types
out, id = au.call(method_name, args_dict, URI)
assert (out==0 or out=="Error: table with that name already exists.")
# TODO: Test that table was created and data was inserted into table
# Test that one model was created
out, id = au.call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
               + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s';" % tablename}, URI)
assert(out[0][0] == 1)
time.sleep(1)

method_name = 'createmodel'
args_dict = dict()
args_dict['tablename'] = tablename
args_dict['number'] = 10
args_dict['iterations'] = 2
out, id = au.call(method_name, args_dict, URI)
assert (out==0)
# Test that inference was started - there should now be two rows of latent states once analyze is finished running.
out, id = au.call('runsql', {'sql_command': "SELECT COUNT(*) FROM preddb.models, preddb.table_index WHERE " \
               + "preddb.models.tableid=preddb.table_index.tableid AND tablename='%s';" % tablename}, URI)
assert(out[0][0] == 2)
time.sleep(1)

method_name = 'select'
args_dict = dict()
args_dict['querystring'] = 'SELECT * FROM %s;' % tablename
out, id = au.call(method_name, args_dict, URI)
csv_results = out
# TODO
# Test that correct things were selected
#assert(csv_results == table_csv)
time.sleep(1)

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

method_name = 'guessschema'
args_dict = dict()
args_dict['tablename'] = tablename
args_dict['csv'] = table_csv
out, id = au.call(method_name, args_dict, URI)
cctypes = out
for value in cctypes:
    assert(value == 'ignore' or value == 'continuous' or value == 'multinomial')
time.sleep(1)

# Clean up: remove test rows from the db
au.call('runsql', {'sql_command': 'DROP TABLE %s;' % tablename}, URI)
out, id = au.call('runsql', {'sql_command': "SELECT tableid FROM preddb.table_index WHERE tablename='%s';" % tablename}, URI)
for result in out:
    tableid = result[0]
    au.call('runsql', {'sql_command': "DELETE FROM preddb.models WHERE tableid=%d " % tableid}, URI)
    au.call('runsql', {'sql_command': "DELETE FROM preddb.table_index WHERE tableid=%d;" % tableid}, URI)

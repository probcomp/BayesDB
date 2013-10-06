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
## TODO: move import to bayesdb project
import tabular_predDB.python_utils.api_utils as au
import inspect
import pickle
import gzip
import prettytable
import re
import os
import time
import ast

from bayesdb.engine.BayesDBEngine import BayesDBEngine, is_int, column_string_splitter
from bayesdb.parser import Parser
bayesdb_engine = BayesDBEngine()
parser = Parser()

class DatabaseClient(object):
    def __init__(self, hostname='localhost', port=8008):
        if hostname is None or hostname=='localhost':
            self.online = False
        else:
            self.online = True
            self.hostname = hostname
            self.port = port
            self.URI = 'http://' + hostname + ':%d' % port


    def set_hostname(self, hostname):
        self.hostname = hostname
        self.URI = 'http://' + self.hostname + ':%d' % self.port

    def get_hostname(self):
        return self.hostname

    def pretty_print(self, query_obj, presql_command=None):
        """If presql_command is None, we must guess"""
        result = ""
        if type(query_obj) == dict and 'data' in query_obj and 'columns' in query_obj:
            pt = prettytable.PrettyTable()
            pt.field_names = query_obj['columns']
            for row in query_obj['data']:
                pt.add_row(row)
            result = pt
        elif type(query_obj) == list and type(query_obj[0]) == tuple:
            pt = prettytable.PrettyTable()
        elif type(query_obj) == dict and 'column_names_reordered' in query_obj:
            colnames = query_obj['column_names_reordered']
            zmatrix = query_obj['z_matrix_reordered']
            pt = prettytable.PrettyTable(hrules=prettytable.ALL, vrules=prettytable.ALL, header=False)
            pt.add_row([''] + list(colnames))
            for row, colname in zip(zmatrix, list(colnames)):
                pt.add_row([colname] + list(row))
            result = pt
        else:
            result = str(query_obj)
        return result

    def __call__(self, sql_string, pretty=True, timing=False):
        return self.execute(sql_string, pretty)

    def execute(self, sql_string, pretty=True, timing=False):
        """
        Call all parse methods.
        If the sql_string does not match, it returns None.
        If the sql_string partially matches enough that we know it's what the user meant, False is returned.
        Otherwise, True is returned for a success, or a Python object may be returned.
        The python object may be printed with pretty_print.
        """
        if timing:
            start_time = time.time()
        asdf = parser.parse(sql_string)
        if sql_string[-1] == ';':
            sql_string = sql_string[:-1]
        words = sql_string.lower().split()
        presql_commands = ['ping',
                           'drop_and_load_db',
                           'drop_tablename',
                           'set_hostname',
                           'get_hostname',
                           'start_from_scratch',
                           'predict',
                           'infer',
                           'analyze',
                           'upload_data_table',
                           'create_model',
                           'update_datatypes',
                           'select',
                           'import_samples',
                           'export_samples',
                           'estimate_dependence_probabilities']
        for presql_command in presql_commands:
            par = getattr(self, 'parse_' + presql_command)
            result = par(words, sql_string)
            if result is None:
                continue

            ## Command matched and executed: now return
            if timing:
                end_time = time.time()
                print 'Elapsed time: %.2f seconds.' % (end_time - start_time)
            if result == False:
                return
            if type(result) == str or not pretty:
                print result
                return result
            else:
                pp = self.pretty_print(result, presql_command)
                print pp
                return pp
        # No predictive sql functions match: attempt to run as sql  
        sql_string = sql_string.lower()
        result = self.runsql(sql_string)
        if pretty:
            pp = self.pretty_print(result, presql_command)
            print pp
            return pp
        else:
            print result
            return result

    def is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False
        
    def call(self, method_name, args_dict):
      if self.online:
        out, id = au.call(method_name, args_dict, self.URI)
      else:
        method = getattr(bayesdb_engine, method_name)
        argnames = inspect.getargspec(method)[0]
        args = [args_dict[argname] for argname in argnames if argname in args_dict]
        out = method(*args)
      return out

    def ping(self):
        return self.call('ping', {})

    def runsql(self, sql_command, order_by=False):
        return self.call('runsql', {'sql_command': sql_command, 'order_by': order_by})

    def start_from_scratch(self):
        return self.call('start_from_scratch', {})

    def drop_and_load_db(self, filename):
        return self.call('drop_and_load_db', {'filename': filename})

    def drop_tablename(self, tablename):
        return self.call('drop_tablename', {'tablename': tablename})

    def delete_chain(self, tablename, chain_index):
        return self.call('delete_chain', {'tablename': tablename, 'chain_index': chain_index})
    
    def upload_data_table(self, tablename, csv, crosscat_column_types):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['csv'] = csv
        args_dict['crosscat_column_types'] = crosscat_column_types
        ret = self.call('upload_data_table', args_dict)
        if type(ret) == dict:
            print 'Created btable %s. Inferred schema:\n' % tablename
        return ret
                              
    def update_datatypes(self, tablename, mappings):
        ret = self.call('update_datatypes', {'tablename':tablename, 'mappings': mappings})
        if type(ret) == dict:
            print 'Updated schema:\n'
        return ret

    def estimate_dependence_probabilities(self, tablename, col, confidence, limit, filename, submatrix):
        ret = self.call('estimate_dependence_probabilities', dict(
                tablename=tablename,
                col=col,
                confidence=confidence,
                limit=limit,
                filename=filename,
                submatrix=submatrix))
        return ret
    
    def create_model(self, tablename, n_chains):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['n_chains'] = n_chains
        return self.call('create_model', args_dict)

    def analyze(self, tablename, chain_index=1, iterations=2, wait=False):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['chain_index'] = chain_index
        args_dict['wait'] = wait
        args_dict['iterations'] = iterations
        return self.call('analyze', args_dict)  

    def infer(self, tablename, columnstring, newtablename, confidence, whereclause, limit, numsamples, order_by):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['columnstring'] = columnstring
        args_dict['newtablename'] = newtablename
        args_dict['whereclause'] = whereclause
        args_dict['confidence'] = confidence
        args_dict['limit'] = limit
        args_dict['numsamples'] = numsamples
        args_dict['order_by'] = order_by
        return self.call('infer', args_dict)

    def select(self, tablename, columnstring, whereclause, limit, order_by):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['columnstring'] = columnstring
        args_dict['whereclause'] = whereclause
        args_dict['limit'] = limit
        args_dict['order_by'] = order_by
        return self.call('select', args_dict)

    def import_samples(self, tablename, X_L_list, X_D_list, M_c, T, iterations=0):
        return self.call('import_samples', {'tablename':tablename,
                                            'X_L_list': X_L_list,
                                            'X_D_list': X_D_list,
                                            'M_c': M_c,
                                            'T': T,
                                            'iterations': iterations})

    def export_samples(self, tablename):
        return self.call('export_samples', {'tablename': tablename})

    def predict(self, tablename, columnstring, newtablename, whereclause, numpredictions, order_by):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['columnstring'] = columnstring
        args_dict['newtablename'] = newtablename
        args_dict['whereclause'] = whereclause
        args_dict['numpredictions'] = numpredictions
        args_dict['order_by'] = order_by
        return self.call('predict', args_dict)

    def write_json_for_table(self, tablename):
        return self.call('write_json_for_table', {'tablename': tablename})

    def create_histogram(self, M_c, data, columns, mc_col_indices, filename):
        args_dict = dict()
        args_dict['M_c'] = M_c
        args_dict['data'] = data
        args_dict['columns'] = columns
        args_dict['mc_col_indices'] = mc_col_indices
        args_dict['filename'] = filename
        return self.call('create_histogram', args_dict)

    def jsonify_and_dump(self, to_dump, filename):
        return self.call('jsonify_and_dump', {'to_dump': to_dump, 'filename': filename})

    def get_metadata_and_table(self, tablename):
        return self.call('get_metadata_and_table', {'tablename': tablename})

    def get_latent_states(self, tablename):
        return self.call('get_latent_states', {'tablename': tablename})

    def gen_feature_z(self, tablename, filename=None, dir=None):
        return self.call('gen_feature_z', {'tablename': tablename, 'filename':filename, 'dir':dir})

    def dump_db(self, filename, dir=None):
        return self.call('dump_db', {'filename':filename, 'dir':dir})

    def guessschema(self, tablename, csv):
        return self.call('guessschema', {'tablename':tablename, 'csv':csv})

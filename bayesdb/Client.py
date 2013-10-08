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
import crosscat.utils.api_utils as au
import inspect
import pickle
import gzip
import prettytable
import re
import os
import time
import ast

from bayesdb.Engine import Engine

class Client(object):
    def __init__(self, hostname=None, port=8008):
        if hostname is None or hostname=='localhost':
            self.online = False
            self.bayesdb_engine = Engine('local')
        else:
            self.online = True
            self.hostname = hostname
            self.port = port
            self.URI = 'http://' + hostname + ':%d' % port

    def call_bayesdb_engine(self, method_name, args_dict):
      if self.online:
        out, id = au.call(method_name, args_dict, self.URI)
      else:
        method = getattr(self.bayesdb_engine, method_name)
        argnames = inspect.getargspec(method)[0]
        args = [args_dict[argname] for argname in argnames if argname in args_dict]
        out = method(*args)
      return out

    def __call__(self, sql_string, pretty=True, timing=False):
        return self.execute(sql_string, pretty)

    def execute(self, sql_string, pretty=True, timing=False):
        if timing:
            start_time = time.time()
            
        result = self.call_bayesdb_engine('execute', dict(bql=sql_string))
        
        if timing:
            end_time = time.time()
            print 'Elapsed time: %.2f seconds.' % (end_time - start_time)
            
        if pretty:
            pp = self.pretty_print(result, presql_command)
            print pp
            return pp
        else:
            return result
        
        '''
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
         '''
        
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




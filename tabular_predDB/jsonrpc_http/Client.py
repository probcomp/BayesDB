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
import tabular_predDB.python_utils.api_utils as au

from tabular_predDB.jsonrpc_http.MiddlewareEngine import MiddlewareEngine
middleware_engine = MiddlewareEngine()

class Client(object):
    def __init__(self, hostname='localhost', port=8008):
        if hostname == None:
            self.online = False
        else:
            self.URI = 'http://' + hostname + ':%d' % port

    def call(self, method_name, args_dict):
      if self.online:
        out, id = au.call(method_name, args_dict, self.URI)
      else:
        method = getattr(middleware_engine, method_name)
        argnames = inspect.getargspec(method)[0]
        args = [args_dict[argname] for argname in argnames if argname in args_dict]
        out = method(*args)
      return out

    def ping(self):
        return self.call('ping', {})

    def runsql(self, sql_command):
        return self.call('runsql', {'sql_command': sql_command})

    def start_from_scratch(self):
        return self.call('start_from_scratch', {})

    def drop_and_load_db(self, filename):
        return self.call('drop_and_load_db', {'filename': filename})

    def drop_tablename(self, tablename):
        return self.call('drop_tablename', {'tablename': tablename})

    def delete_chain(self, tablename, chain_index):
        return self.call('delete_chain', {'tablename': tablename})
    
    def upload_data_table(self, tablename, csv, crosscat_column_types):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['csv'] = table_csv 
        args_dict['crosscat_column_types'] = crosscat_column_types
        return self.call('upload_data_table', args_dict)

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

    def infer(self, tablename, columnstring, newtablename, confidence, whereclause, limit, numsamples):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['columnstring'] = columnstring
        args_dict['newtablename'] = newtablename
        args_dict['whereclause'] = whereclause
        args_dict['confidence'] = confidence
        args_dict['limit'] = limit
        args_dict['numsamples'] = numsamples
        return self.call('infer', args_dict)

    def predict(self, tablename, columnstring, newtablename, whereclause, numpredictions):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['columnstring'] = columnstring
        args_dict['newtablename'] = newtablename
        args_dict['whereclause'] = whereclause
        args_dict['numpredictions'] = numpredictions
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

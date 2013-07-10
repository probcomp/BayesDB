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

class DatabaseClient(object):
    def __init__(self, hostname='localhost', port=8008):
        if hostname == None:
            self.online = False
        else:
            self.hostname = hostname
            self.port = port
            self.URI = 'http://' + hostname + ':%d' % port

    def parse_set_hostname(self, words):
        if len(words) >= 3:
            if words[0] == 'set' and words[1] == 'hostname':
                self.set_hostname(words[2])
        return False

    def set_hostname(self, hostname):
        self.hostname = hostname
        self.URI = 'http://' + self.hostname + ':%d' % self.port

    def parse_get_hostname(self, words):
        if len(words) >= 2 and words[0] == 'get' and words[1] == 'hostname':
            return {}
        return False

    def get_hostname(self):
        return self.hostname

    def parse_ping(self, words):
        if len(words) >= 1 and words[0] == 'ping':
            return {}
        else:
            return False

    def parse_start_from_scratch(self, words):
        if len(words) >= 3:
            if words[0] == 'start' and words[1] == 'from' and words[2] == 'scratch':
                return {}
        return False

    def parse_drop_and_load_db(self, words):
        if len(words) >= 2:
            if words[0] == 'drop' and words[1] == 'and' and words[2] == 'load':
                if len(words) == 3:
                    return {'filename': words[3]}
                else:
                    print 'Did you mean: DROP AND LOAD <filename>;?'
        return False

    def parse_create_model(self, words):
        n_chains = 10
        if len(words) >=1:
            if words[0] == 'create':
                if len(words) >= 4 and words[1] == 'model' or words[1] == 'models':
                    if words[2] == 'for':
                        tablename = words[3]
                        if len(words) >= 7:
                            if words[4] == 'with' and self.is_int(words[5]) and words[6] == 'explanations':
                                n_chains = int(words[5])
                        return {'tablename': tablename, 'n_chains': n_chains}
                    else:
                        print 'Did you mean: CREATE MODELS FOR <ptable> [WITH <n_chains> EXPLANATIONS];?'
                elif len(words) >= 3 and self.is_int(words[1]):
                    n_chains = int(words[1])
                    assert n_chains > 0
                    if words[2] == 'model' or words[2] == 'models':
                        if len(words) >= 5 and words[3] == 'for':
                            tablename = words[4]
                            return {'tablename': tablename, 'n_chains': n_chains}
                        else:
                            print 'Did you mean: CREATE <n_chains> MODELS FOR <ptable>;?'
                else:
                    print 'Did you mean: CREATE <n_chains> MODELS FOR <ptable>;?'
        return False

    def parse_upload_data_table(self, words):
        args_dict = dict()
        args_dict['crosscat_column_types'] = {}
        words = sql_string.split()
        if len(words) >= 2:
            if (words[0] == 'upload' or words[0] == 'create') and words[1] == 'ptable':
                if len(words) >= 5:
                    args_dict['tablename'] = words[2]
                    if words[3] == 'from':
                        try:
                            f = open(words[4], 'r')
                            args_dict['csv'] = f.read()
                        except:
                            return 'Invalid file.'
                else:
                    print 'Did you mean: CREATE PTABLE <tablename> FROM <filename>;?'
        return False

    def parse_drop_tablename(self, words):
        if len(words) >= 3:
            if words[0] == 'drop' and words[1] == 'tablename':
                return {'tablename': words[2])
        return False

    def parse_delete_chain(self, words):
        # TODO: specifying chain doesn't do anything
        args_dict = dict()
        if len(words) >= 3:
            if words[0] == 'delete':
                if words[1] == 'chain' and self.is_int(words[2]):
                    args_dict['chain_index'] = int(words[2])
                    if words[3] == 'from':
                        args_dict['tablename'] = words[4]
                        return args_dict
                elif len(words) >= 6 and words[2] == 'all' and words[3] == 'chains' and words[4] == 'from':
                    args_dict['chain_index'] = 'all'
                    args_dict['tablename'] = words[5]
                    return args_dict
                else:
                    print 'Did you mean: DELETE CHAIN <chain_index> FROM <tablename>;?'
        return False

    def parse_analyze(self, words):
        args_dict = dict()
        args_dict['chain_index'] = 'all'
        args_dict['iterations'] = 2
        args_dict['wait'] = False
        if len(words) >= 1 and words[0] == 'analyze':
            if len(words) >= 2:
                args_dict['tablename'] = words[1]
            else:
                print 'Did you mean: ANALYZE <ptable> [CHAIN INDEX <chain_index>] [FOR <iterations> ITERATIONS];?'
            idx = 2
            if words[idx] == "chain" and words[idx+1] == 'index':
                args_dict['chain_index'] = words[idx+2]
                idx += 3
            ## TODO: check length here
            if words[idx] == "for" and words[idx+2] == 'iterations':
                args_dict['iterations'] = words[idx+1]
            return args_dict

    def parse_infer(self, words):
        args_dict = dict()

        args_dict['newtablename'] = newtablename
        args_dict['whereclause'] = whereclause
        args_dict['confidence'] = confidence
        args_dict['limit'] = limit
        args_dict['numsamples'] = numsamples
        if words[0] == 'infer':
            idx = 1
            cols = []
            cols.append(words[idx])
            while ',' in words[idx] and len(words) > idx + 1:
                idx += 1
                cols.append(words[idx])
            if len(words) > idx and words[idx + 1] == 'from':
                args_dict['columnstring'] = ' '.join(cols)
                args_dict['tablename'] = words[idx + 2]
                
                idx = idx + 3
                if words[idx + 3] == 'where':
                    where = []
                    ## use python sqlparse?
                ## TODO: parse where, confidence, etc. here
            else:
                print 'Did you mean: INFER col0, [col1, ...] FROM <ptable> [WHERE <whereclause>] '+\
                    'WITH CONFIDENCE <confidence> [LIMIT <limit>] [NUMSAMPLES <numsamples>] [ORDER BY similarity(row_id, [col])];?'

    def parse_predict(self, words):
        args_dict = dict()
        args_dict['tablename'] = tablename
        args_dict['columnstring'] = columnstring
        args_dict['newtablename'] = newtablename
        args_dict['whereclause'] = whereclause
        args_dict['numpredictions'] = numpredictions
        print 'Did you mean: SIMULATE col0, [col1, ...] FROM <ptable> [WHERE <whereclause>] TIMES <times> '+\
            '[ORDER BY similarity(row_id, [col])];?'

    def parse_write_json_for_table(self, words):
        if len(words) >= 5:
            if words[0] == 'write' and words[1] == 'json' and words[2] == 'for' and words[3] == 'table':
                return {'tablename': words[4]}
        return False        

    def parse_create_histogram(self, words):
        args_dict = dict()
        args_dict['M_c'] = M_c
        args_dict['data'] = data
        args_dict['columns'] = columns
        args_dict['mc_col_indices'] = mc_col_indices
        args_dict['filename'] = filename

    ## TODO: fix all these
    def parse_jsonify_and_dump(self, words):
        return self.call('jsonify_and_dump', {'to_dump': to_dump, 'filename': filename})

    def parse_get_metadata_and_table(self, tablename):
        return self.call('get_metadata_and_table', {'tablename': tablename})

    def parse_get_latent_states(self, tablename):
        return self.call('get_latent_states', {'tablename': tablename})

    def parse_gen_feature_z(self, tablename, filename=None, dir=None):
        return self.call('gen_feature_z', {'tablename': tablename, 'filename':filename, 'dir':dir})

    def parse_dump_db(self, filename, dir=None):
        return self.call('dump_db', {'filename':filename, 'dir':dir})

    def parse_guessschema(self, tablename, csv):
        return self.call('guessschema', {'tablename':tablename, 'csv':csv})
    
    
    def execute(self, sql_string):
        if sql_string[-1] == ';':
            sql_string = sql_string[:-1]
        words = sql_string.lower().split()
        presql_commands = ['ping',
                          'drop_and_load_db']
        for presql_command in presql_commands:
            parser = getattr(self, 'parse_' + presql_command)
            args_dict = parser(words)
            if args_dict:
                return self.call(presql_command, args_dict)
        # No predictive sql functions match: attempt to run as sql  
        self.runsql(sql_string)

    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False
        

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
        return self.call('delete_chain', {'tablename': tablename, 'chain_index': chain_index})
    
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

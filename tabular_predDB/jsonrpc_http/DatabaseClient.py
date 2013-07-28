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
import inspect
import prettytable
import re

from tabular_predDB.jsonrpc_http.MiddlewareEngine import MiddlewareEngine
middleware_engine = MiddlewareEngine()

class DatabaseClient(object):
    def __init__(self, hostname='localhost', port=8008):
        if hostname == None:
            self.online = False
        else:
            self.online = True
            self.hostname = hostname
            self.port = port
            self.URI = 'http://' + hostname + ':%d' % port

    def parse_set_hostname(self, words, orig):
        if len(words) >= 3:
            if words[0] == 'set' and words[1] == 'hostname':
                return self.set_hostname(words[2])

    def set_hostname(self, hostname):
        self.hostname = hostname
        self.URI = 'http://' + self.hostname + ':%d' % self.port

    def parse_get_hostname(self, words, orig):
        if len(words) >= 2 and words[0] == 'get' and words[1] == 'hostname':
            return self.get_hostname()

    def get_hostname(self):
        return self.hostname

    def parse_ping(self, words, orig):
        if len(words) >= 1 and words[0] == 'ping':
            return self.ping()

    def parse_start_from_scratch(self, words, orig):
        if len(words) >= 3:
            if words[0] == 'start' and words[1] == 'from' and words[2] == 'scratch':
                return self.start_from_scratch()

    def parse_drop_and_load_db(self, words, orig):
        if len(words) >= 2:
            if words[0] == 'drop' and words[1] == 'and' and words[2] == 'load':
                if len(words) == 3:
                    return self.drop_and_load_db(words[3])
                else:
                    print 'Did you mean: DROP AND LOAD <filename>;?'
                    return False

    def parse_create_model(self, words, orig):
        n_chains = 10
        if len(words) >=1:
            if words[0] == 'create':
                if len(words) >= 4 and words[1] == 'model' or words[1] == 'models':
                    if words[2] == 'for':
                        tablename = words[3]
                        if len(words) >= 7:
                            if words[4] == 'with' and self.is_int(words[5]) and words[6] == 'explanations':
                                n_chains = int(words[5])
                        result = self.create_model(tablename, n_chains)
                        print 'Created %d models for ptable %s' % (n_chains, tablename)
                        return result
                    else:
                        print 'Did you mean: CREATE MODELS FOR <ptable> [WITH <n_chains> EXPLANATIONS];?'
                        return False
                elif len(words) >= 3 and self.is_int(words[1]):
                    n_chains = int(words[1])
                    assert n_chains > 0
                    if words[2] == 'model' or words[2] == 'models':
                        if len(words) >= 5 and words[3] == 'for':
                            tablename = words[4]
                            result = self.create_model(tablename, n_chains)
                            print 'Created %d models for ptable %s' % (n_chains, tablename)
                            return result
                        else:
                            print 'Did you mean: CREATE <n_chains> MODELS FOR <ptable>;?'
                            return False
                else:
                    print 'Did you mean: CREATE <n_chains> MODELS FOR <ptable>;?'
                    return False

    def parse_upload_data_table(self, words, orig):
        crosscat_column_types = None
        if len(words) >= 2:
            if (words[0] == 'upload' or words[0] == 'create') and words[1] == 'ptable':
                if len(words) >= 5:
                    tablename = words[2]
                    if words[3] == 'from':
                        try:
                            f = open(orig.split()[4], 'r')
                            csv = f.read()
                            result = self.upload_data_table(tablename, csv, crosscat_column_types)
                            print 'Created ptable %s' % tablename
                            return result
                        except Exception as e:
                            print str(e)
                            return False
                else:
                    print 'Did you mean: CREATE PTABLE <tablename> FROM <filename>;?'
                    return False

    def parse_drop_tablename(self, words, orig):
        if len(words) >= 3:
            if words[0] == 'drop' and (words[1] == 'tablename' or words[1] == 'ptable'):
                return self.drop_tablename(words[2])

    def parse_delete_chain(self, words, orig):
        if len(words) >= 3:
            if words[0] == 'delete':
                if words[1] == 'chain' and self.is_int(words[2]):
                    chain_index = int(words[2])
                    if words[3] == 'from':
                        tablename = words[4]
                        return self.delete_chain(tablename, chain_index)
                elif len(words) >= 6 and words[2] == 'all' and words[3] == 'chains' and words[4] == 'from':
                    chain_index = 'all'
                    tablename = words[5]
                    return self.delete_chain(tablename, chain_index)
                else:
                    print 'Did you mean: DELETE CHAIN <chain_index> FROM <tablename>;?'
                    return False

    def parse_select(self, words, orig):
        pass

    def parse_order_by_similarity(self, words, orig):
        match = re.search(r'order by similarity\((\w*?)((,\s+?)(\w*?))?\)', orig.lower())
        if words[0] == 'select' and match:
            try:
                row_id = int(m.groups()[0])
                col_id = m.groups()[3]
                if not col is None:
                    col = int(col)
            except ValueError:
                print "Similarity's arguments must be integers."
            

    def parse_analyze(self, words, orig):
        chain_index = 'all'
        iterations = 2
        wait = False
        if len(words) >= 1 and words[0] == 'analyze':
            if len(words) >= 2:
                tablename = words[1]
            else:
                print 'Did you mean: ANALYZE <ptable> [CHAIN INDEX <chain_index>] [FOR <iterations> ITERATIONS];?'
                return False
            idx = 2
            if words[idx] == "chain" and words[idx+1] == 'index':
                chain_index = words[idx+2]
                idx += 3
            ## TODO: check length here
            if words[idx] == "for" and words[idx+2] == 'iterations':
                iterations = int(words[idx+1])
            return self.analyze(tablename, chain_index, iterations, wait=False)

    def parse_infer(self, words, orig):
        match = re.search(r"""
            infer\s+
            (?P<columnstring>[^\s,]+(?:,\s*[^\s,]+)*)\s+
            from\s+(?P<btable>[^\s]+)\s+
            (where\s+(?P<whereclause>.*(?=with)))?
            with\s+confidence\s+(?P<confidence>[^\s]+)
            (\s+limit\s+(?P<limit>[^\s]+))?
            (\s+numsamples\s+(?P<numsamples>[^\s]+))?;?'
        """, orig.lower(), re.VERBOSE)
        if match is None:
            if words[0] == 'infer':
                print 'Did you mean: INFER col0, [col1, ...] FROM <ptable> [WHERE <whereclause>] '+\
                    'WITH CONFIDENCE <confidence> [LIMIT <limit>] [NUMSAMPLES <numsamples>] [ORDER BY similarity(row_id, [col])];?'
                return False
            else:
                return None
        else:
            columnstring = match.group('columnstring').strip()
            tablename = match.group('btable')
            whereclause = match.group('whereclause').strip()
            if whereclause is None:
                whereclause = ''
            confidence = float(match.group('confidence'))
            limit = match.group('limit')
            if limit is None:
                limit = Float("inf")
            else:
                limit = int(limit)
            numsamples = match.group('numsamples')
            if numsamples is None:
                numsamples = 1
            else:
                numsamples = int(numsamples)
            newtablename = '' # For INTO
            return self.infer(tablename, columnstring, newtablename, confidence, whereclause, limit, numsamples)

    def parse_predict(self, words, orig):
        match = re.search(r"""
            simulate\s+
            (?P<columnstring>[^\s,]+(?:,\s*[^\s,]+)*)\s+
            from\s+(?P<btable>[^\s]+)\s+
            (where\s+(?P<whereclause>.*(?=times)))?
            times\s+(?P<times>[^\s]+)
        """, orig.lower(), re.VERBOSE)
        if match is None:
            if words[0] == 'simulate':
                print 'Did you mean: SIMULATE col0, [col1, ...] FROM <ptable> [WHERE <whereclause>] TIMES <times> '+\
                    '[ORDER BY similarity(row_id, [col])];?'
                return False
            else:
                return None
        else:
            columnstring = match.group('columnstring').strip()
            tablename = match.group('btable')
            whereclause = match.group('whereclause').strip()
            print 'whereclause:',whereclause
            if whereclause is None:
                whereclause = ''
            numpredictions = int(match.group('times'))
            newtablename = '' # For INTO
            return self.predict(tablename, columnstring, newtablename, whereclause, numpredictions)

    def parse_update_datatypes(self, words, orig):
        match = re.search(r"""
            update\s+datatypes\s+from\s+
            (?P<btable>[^\s]+)\s+
            set\s+(?P<mappings>[^;]*);?
        """, orig.lower(), re.VERBOSE)
        if match is None:
            if words[0] == 'update':
                print 'Did you mean: UPDATE DATATYPES FROM <btable> SET [col0=numerical|categorical[(k)]]+;?'
                return False
            else:
                return None
        else:
            tablename = match.group('btable').strip()
            mapping_string = match.group('mappings').strip()
            mappings = dict()
            for mapping in mapping_string.split(','):
                vals = mapping.split('=')
                if 'continuous' in vals[1] or 'numerical' in vals[1]:
                    datatype = 'continuous'
                elif 'multinomial' in vals[1] or 'categorical' in vals[1]:
                    m = re.search(r'\((?P<num>[^\)]+)\)', vals[1])
                    if m:
                        datatype = int(m.group('num'))
                    else:
                        datatype = 'multinomial'
                elif 'ignore' in vals[1]:
                    datatype = 'ignore'
                else:
                    print 'Did you mean: UPDATE DATATYPES FROM <btable> SET [col0=numerical|categorical[(k)]]+;?'
                    return False
                mappings[vals[0]] = datatype
            return self.update_datatypes(tablename, mappings)

    def parse_write_json_for_table(self, words, orig):
        if len(words) >= 5:
            if words[0] == 'write' and words[1] == 'json' and words[2] == 'for' and words[3] == 'table':
                return {'tablename': words[4]}

    def parse_create_histogram(self, words, orig):
        '''TODO'''
        args_dict = dict()
        M_c = M_c
        data = data
        columns = columns
        mc_col_indices = mc_col_indices
        filename = filename

    ## TODO: fix all these
    def parse_jsonify_and_dump(self, words, orig):
        '''TODO'''
        pass
        #return self.call('jsonify_and_dump', {'to_dump': to_dump, 'filename': filename})

    def parse_get_metadata_and_table(self, tablename):
        '''TODO'''
        pass
        #return self.call('get_metadata_and_table', {'tablename': tablename})

    def parse_get_latent_states(self, tablename):
        pass
        #return self.call('get_latent_states', {'tablename': tablename})

    def parse_gen_feature_z(self, tablename, filename=None, dir=None):
        pass
        #return self.call('gen_feature_z', {'tablename': tablename, 'filename':filename, 'dir':dir})

    def parse_dump_db(self, filename, dir=None):
        pass
        #return self.call('dump_db', {'filename':filename, 'dir':dir})

    def parse_guessschema(self, tablename, csv):
        pass
        #return self.call('guessschema', {'tablename':tablename, 'csv':csv})
    
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
        else:
            result = str(query_obj)
        return result
    
    def execute(self, sql_string, pretty=True):
        """
        Call all parse methods.
        If the sql_string does not match, it returns None.
        If the sql_string partially matches enough that we know it's what the user meant, False is returned.
        Otherwise, True is returned for a success, or a Python object may be returned.
        The python object may be printed with pretty_print.
        """
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
                           'update_datatypes']
        for presql_command in presql_commands:
            parser = getattr(self, 'parse_' + presql_command)
            result = parser(words, sql_string)
            if result is None:
                continue
            if result == False:
                return
            if type(result) == str or not pretty:
                return result
            else:
                return self.pretty_print(result, presql_command)
        # No predictive sql functions match: attempt to run as sql  
        sql_string = sql_string.lower()
        result = self.runsql(sql_string)
        if pretty:
            return self.pretty_print(result, presql_command)
        else:
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
        args_dict['csv'] = csv
        args_dict['crosscat_column_types'] = crosscat_column_types
        ret = self.call('upload_data_table', args_dict)
        print 'Created btable %s. Inferred schema:\n' % tablename
        return ret
                              
    def update_datatypes(self, tablename, mappings):
        ret = self.call('update_datatypes', {'tablename':tablename, 'mappings': mappings})
        print 'Updated schema:\n'
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

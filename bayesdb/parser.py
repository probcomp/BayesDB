#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import engine as be
import re
import pickle
import gzip
import utils
import os

class Parser(object):
    def __init__(self):
        self.engine_method_names = [method_name for method_name in be.get_method_names() if method_name[0] != '_']
        self.parser_method_names = [method_name[6:] for method_name in dir(Parser) if method_name[:6] == 'parse_']
        self.method_names = set(self.engine_method_names).intersection(self.parser_method_names)
        self.method_name_to_args = be.get_method_name_to_args()
        self.reset_root_dir()
    
    def parse(self, bql_string):
        """
        Accepts a large chunk of BQL (such as a file containing many BQL statements)
        as a string, and returns individual SQL statements as a list of strings.

        Uses semicolons to split statements.
        """
        ret_statements = []
        if len(bql_string) == 0:
            return
        bql_string = re.sub(r'--.*?\n', '', bql_string)
        lines = bql_string.split(';')
        for line in lines:
            if '--' in line:
                line = line[:line.index('--')]
            line = line.strip()
            if line is not None and len(line) > 0:
                ret_statements.append(line)
        return ret_statements
    
    def parse_statement(self, bql_statement_string):
        """
        Accepts an individual BQL statement as a string, and parses it.

        If the input can be parsed into a valid BQL statement, then the tuple
        (method_name, arguments_dict) is returned, which corresponds to the
        Engine method name and arguments that should be called to execute this statement.

        If the input is not a valid BQL statement, False or None is returned.
        
        False indicates that the user was close to a valid command, but has slightly
        incorrect syntax for the arguments. In this case, a helpful message will be printed.
        
        None indicates that no good match for the command was found.
        """
        if len(bql_statement_string) == 0:
            return
        if bql_statement_string[-1] == ';':
            bql_statement_string = bql_statement_string[:-1]
        words = bql_statement_string.lower().split()

        if len(words) >= 1 and words[0] == 'help':
            print "Welcome to BQL help. Here is a list of BQL commands and their syntax:\n"
            for method_name in sorted(self.method_names):
                help_method = getattr(self, 'help_' +  method_name)
                print help_method()
            return False

        help_strings_to_print = list()
        for method_name in self.method_names:
            parse_method = getattr(self, 'parse_' + method_name)
            result = parse_method(words, bql_statement_string)
            if result is not None:
                if result[0] == 'help':
                    help_strings_to_print.append(result[1])
                else:
                    return result

        for help_string in help_strings_to_print:
            print help_string

    def set_root_dir(self, root_dir):
        """Set the root_directory, used as the base for all relative paths."""
        self.root_directory = root_dir

    def reset_root_dir(self):
        """Set the root_directory, used as the base for all relative paths, to
        the current working directory."""        
        self.root_directory = os.getcwd()

    def get_absolute_path(self, relative_path):
        """
        If a relative file path is given by the user in a command,
        this method is used to convert the path to an absolute path
        by assuming that the correct base directory is self.root_directory.
        """
        if os.path.isabs(relative_path):
            return relative_path
        else:
            return os.path.join(self.root_directory, relative_path)

##################################################################################
# Methods to parse individual commands (and the associated help method with each)
##################################################################################

    def help_list_btables(self):
        return "LIST BTABLES: view the list of all btable names."

    def parse_list_btables(self, words, orig):
        if len(words) >= 2:
            if words[0] == 'list' and words[1] == 'btables':
                return 'list_btables', dict()


    def help_execute_file(self):
        return "EXECUTE FILE <filename>: execute a BQL script from file."

    def parse_execute_file(self, words, orig):
        if len(words) >= 2 and words[0] == 'execute':
            if len(words) >= 3 and words[1] == 'file':
                filename = words[1]
                return 'execute_file', dict(filename=self.get_absolute_path(filename))
            else:
                return 'help', self.help_execute_file()

                
    def help_show_schema(self):
        return "SHOW SCHEMA FOR <btable>: show the datatype schema for the btable."

    def parse_show_schema(self, words, orig):
        if len(words) >= 4 and words[0] == 'show' and words[1] == 'schema':
            if words[2] == 'for':
                return 'show_schema', dict(tablename=words[3])
            else:
                return 'help', self.help_show_schema()

                
    def help_show_models(self):
        return "SHOW MODELS FOR <btable>: show the models and iterations stored for btable."

    def parse_show_models(self, words, orig):
        if len(words) >= 4 and words[0] == 'show' and words[1] == 'models':
            if words[2] == 'for':
                return 'show_models', dict(tablename=words[3])
            else:
                return 'help', self.help_show_models()

                
    def help_show_diagnostics(self):
        return "SHOW DIAGNOSTICS FOR <btable>: show diagnostics for this btable's models."

    def parse_show_diagnostics(self, words, orig):
        if len(words) >= 4 and words[0] == 'show' and words[1] == 'diagnostics':
            if words[2] == 'for':
                return 'show_diagnostics', dict(tablename=words[3])
            else:
                return 'help', self.help_show_diagnostics()


    def help_drop_models(self):
        return "DROP MODELS [<min> TO <max>] FOR <btable>: drop the models specified by the given ids."

    def parse_drop_models(self, words, orig):
        ## TODO: parse min to max
        if len(words) >= 4 and words[0] == 'models' and words[1] == 'drop':
            if words[2] == 'for':
                return 'drop_models', dict(tablename=words[3])
            else:
                return 'help', self.help_show_diagnostics()
                
                
    def help_initialize_models(self):
        return "INITIALIZE <num_models> MODELS FOR <btable> [WITH CONFIG <model_config>]: the step to perform before analyze."

    def parse_initialize_models(self, words, orig):
        match = re.search(r"""
            initialize\s+
            (?P<num_models>[^\s]+)
            \s+model(s)?\s+for\s+
            (?P<btable>[^\s]+)
            (\s+with\s+config\s+(?P<model_config>)$)?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'initialize' or words[0] == 'create':
                return 'help', self.help_initialize_models()
        else:
            n_models = int(match.group('num_models'))
            tablename = match.group('btable')
            model_config = match.group('model_config')

            if model_config is not None:
                model_config = model_config.strip()
            return 'initialize_models', dict(tablename=tablename, n_models=n_models,
                                             model_config=model_config)
                    
    def help_create_btable(self):
        return "CREATE BTABLE <tablename> FROM <filename>: create a table from a csv file"

    def parse_create_btable(self, words, orig):
        crosscat_column_types = None
        if len(words) >= 2:
            if (words[0] == 'upload' or words[0] == 'create') and (words[1] == 'ptable' or words[1] == 'btable'):
                if len(words) >= 5:
                    tablename = words[2]
                    if words[3] == 'from':
                        f = open(self.get_absolute_path(orig.split()[4]), 'r')
                        csv = f.read()
                        result = ('create_btable',
                                 dict(tablename=tablename, csv=csv,
                                      crosscat_column_types=crosscat_column_types))
                        return result
                else:
                    return 'help', self.help_create_btable()


                    
    def help_drop_btable(self):
        return "DROP BTABLE <tablename>: drop table."

    def parse_drop_btable(self, words, orig):
        if len(words) >= 3:
            if words[0] == 'drop' and (words[1] == 'tablename' or words[1] == 'ptable' or words[1] == 'btable'):
                return 'drop_btable', dict(tablename=words[2])


                
    def help_drop_models(self):
        return "DROP MODEL[S| <model_index>] FROM <tablename>: delete the model with specified index, or all models."

    def parse_drop_models(self, words, orig):
        if len(words) >= 3:
            if words[0] == 'delete':
                if words[1] == 'model' and utils.is_int(words[2]):
                    model_index = int(words[2])
                    if words[3] == 'from':
                        tablename = words[4]
                        return 'drop_models', dict(tablename=tablename, model_index=model_index)
                elif len(words) >= 5 and (words[2] == 'models' and words[3] == 'from'):
                    model_index = 'all'
                    tablename = words[4]
                    return 'drop_models', dict(tablename=tablename, model_index=model_index)
                else:
                    return 'help', self.help_drop_models()


                    
    def help_analyze(self):
        return "ANALYZE <btable> [MODEL INDEX <model_index>] [FOR <iterations> ITERATIONS | FOR <seconds> SECONDS]: perform inference."

    def parse_analyze(self, words, orig):
        model_index = 'all'
        iterations = None
        seconds = None
        if len(words) >= 1 and words[0] == 'analyze':
            if len(words) >= 2:
                tablename = words[1]
            else:
                return 'help', self.help_analyze()
            idx = 2
            if words[idx] == "model" and words[idx+1] == 'index':
                model_index = words[idx+2]
                idx += 3
            ## TODO: check length here
            if words[idx] == "for" and ((words[idx+2] == 'iterations') or (words[idx+2] == 'iteration')):
                iterations = int(words[idx+1])
                seconds = -1
            elif words[idx] == "for" and ((words[idx+2] == 'seconds') or (words[idx+2] == 'second')):
                seconds = float(words[idx+1])
                iterations = None
            else:
                seconds = 300
                iterations = None
            return 'analyze', dict(tablename=tablename, model_index=model_index,
                                   iterations=iterations, seconds=seconds)


            
    def help_infer(self):
        return "INFER [HIST] col0, [col1, ...] FROM <btable> [WHERE <whereclause>] WITH CONFIDENCE <confidence> [LIMIT <limit>] [NUMSAMPLES <numsamples>] [ORDER BY SIMILARITY TO <row_id> [WITH RESPECT TO <column>]] [SAVE TO <file>]: like select, but infers (fills in) missing values."
        
    def parse_infer(self, words, orig):
        match = re.search(r"""
            infer\s+
            (?P<hist>hist\s+)?        
            (?P<columnstring>[^\s,]+(?:,\s*[^\s,]+)*)\s+
            from\s+(?P<btable>[^\s]+)\s+
            (where\s+(?P<whereclause>.*(?=with)))?
            \s*with\s+confidence\s+(?P<confidence>[^\s]+)
            (\s+limit\s+(?P<limit>[^\s]+))?
            (\s+numsamples\s+(?P<numsamples>[^\s]+))?
            (\s+save\s+to\s+(?P<filename>[^\s]+))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'infer':
                return 'help', self.help_infer()
        else:
            columnstring = match.group('columnstring').strip()
            tablename = match.group('btable')
            whereclause = match.group('whereclause')
            if whereclause is None:
                whereclause = ''
            else:
                whereclause = whereclause.strip()
            confidence = float(match.group('confidence'))
            limit = match.group('limit')
            if limit is None:
                limit = float("inf")
            else:
                limit = int(limit)
            numsamples = match.group('numsamples')
            if numsamples is None:
                numsamples = 1
            else:
                numsamples = int(numsamples)
            newtablename = '' # For INTO
            orig, order_by = self.extract_order_by(orig)
            hist = match.group('hist') is not None
            if match.group('filename'):
                filename = match.group('filename')
            else:
                filename = None
            return 'infer', \
                   dict(tablename=tablename, columnstring=columnstring, newtablename=newtablename,
                        confidence=confidence, whereclause=whereclause, limit=limit,
                        numsamples=numsamples, order_by=order_by, hist=hist), \
                   dict(hist=hist, filename=filename)

            
            
    def help_save_models(self):
        return "SAVE MODELS FROM <btable> TO <pklpath>: save your models to a pickle file."

    def parse_save_models(self, words, orig):
        match = re.search(r"""
            save\s+
            (models\s+)?
            ((from\s+)|(for\s+))
            (?P<btable>[^\s]+)
            \s+to\s+
            (?P<pklpath>[^\s]+)
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'save':
                return 'help', self.help_save_models()
        else:
            tablename = match.group('btable')
            pklpath = match.group('pklpath')
            if pklpath[-7:] != '.pkl.gz':
                if pklpath[-4:] == '.pkl':
                    pklpath = pklpath + ".gz"
                else:
                    pklpath = pklpath + ".pkl.gz"
            return 'save_models', dict(tablename=tablename), dict(pkl_path=pklpath)


            
    def help_load_models(self):
        return "LOAD MODELS <pklpath> INTO <btable>: load models from a pickle file."
        
    def parse_load_models(self, words, orig):
        match = re.search(r"""
            load\s+
            models\s+
            (?P<pklpath>[^\s]+)\s+
            ((into\s+)|(for\s+))
            (?P<btable>[^\s]+)
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'load':
                return 'help', self.help_load_models()
        else:
            tablename = match.group('btable')
            pklpath = match.group('pklpath')
            try:
                ## TODO: remove this code that actually does stuff from the parser...                
                models = pickle.load(gzip.open(self.get_absolute_path(pklpath), 'rb'))
            except IOError as e:
                if pklpath[-7:] != '.pkl.gz':
                    if pklpath[-4:] == '.pkl':
                        models = pickle.load(open(self.get_absolute_path(pklpath), 'rb'))
                    else:
                        pklpath = pklpath + ".pkl.gz"
                        models = pickle.load(gzip.open(self.get_absolute_path(pklpath), 'rb'))
                else:
                    raise e
            return 'load_models', dict(tablename=tablename, models=models)


            
    def help_select(self):
        return 'SELECT [HIST] <columns|functions> FROM <btable> [WHERE <whereclause>]  [ORDER BY <columns>] [LIMIT <limit>] [SAVE TO <file>]'
        
    def parse_select(self, words, orig):
        match = re.search(r"""
            select\s+
            (?P<hist>hist\s+)?        
            (?P<columnstring>.*?((?=from)))
            \s*from\s+(?P<btable>[^\s]+)\s*
            (where\s+(?P<whereclause>.*?((?=limit)|(?=order)|$)))?
            (\s*limit\s+(?P<limit>[^\s]+))?
            (\s+save\s+to\s+(?P<filename>[^\s]+))?        
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'select':
                return 'help', self.help_select()
        else:
            columnstring = match.group('columnstring').strip()
            tablename = match.group('btable')
            whereclause = match.group('whereclause')
            if whereclause is None:
                whereclause = ''
            else:
                whereclause = whereclause.strip()
            limit = self.extract_limit(orig)
            orig, order_by = self.extract_order_by(orig)
            hist = match.group('hist') is not None
            if match.group('filename'):
                filename = match.group('filename')
            else:
                filename = None
            return 'select', dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
                                  limit=limit, order_by=order_by, hist=hist), dict(hist=hist, filename=filename)


    def help_simulate(self):
        return "SIMULATE [HIST] col0, [col1, ...] FROM <btable> [GIVEN <givens>] TIMES <times> [SAVE TO <file>]: simulate new datapoints based on the underlying model."

    def parse_simulate(self, words, orig):
        match = re.search(r"""
            simulate\s+
            (?P<hist>hist\s+)?
            (?P<columnstring>[^\s,]+(?:,\s*[^\s,]+)*)\s+
            from\s+(?P<btable>[^\s]+)\s+
            ((given|where)\s+(?P<givens>.*(?=times)))?
            times\s+(?P<times>[^\s]+)
            (\s+save\s+to\s+(?P<filename>[^\s]+))?        
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'simulate':
                return 'help', self.help_simulate()
        else:
            columnstring = match.group('columnstring').strip()
            tablename = match.group('btable')
            givens = match.group('givens')
            if givens is None:
                givens = ''
            else:
                givens = givens.strip()
            numpredictions = int(match.group('times'))
            newtablename = '' # For INTO
            orig, order_by = self.extract_order_by(orig)
            hist = match.group('hist') is not None
            if match.group('filename'):
                filename = match.group('filename')
            else:
                filename = None            
            return 'simulate', \
                    dict(tablename=tablename, columnstring=columnstring, newtablename=newtablename,
                         givens=givens, numpredictions=numpredictions, order_by=order_by, hist=hist), \
                    dict(hist=hist, filename=filename)

    def help_show_column_lists(self):
        return "SHOW COLUMN LISTS FOR <btable>"

    def parse_show_column_lists(self, words, orig):
        match = re.search(r"""
          SHOW\s+COLUMN\s+LISTS\s+FOR\s+
          (?P<btable>[^\s]+)
        """, orig, flags=re.VERBOSE|re.IGNORECASE)
        if not match:
            if words[0] == 'show':
                return 'help', self.help_show_column_lists()
        else:
            tablename = match.group('btable')
            return 'show_column_lists', dict(tablename=tablename)

    def help_show_columns(self):
        return "SHOW COLUMNS <column_list> FROM <btable>"

    def parse_show_columns(self, words, orig):
        match = re.search(r"""
          SHOW\s+COLUMNS\s+
          ((?P<columnlist>[^\s]+)\s+)?
          FROM\s+
          (?P<btable>[^\s]+)
        """, orig, flags= re.VERBOSE | re.IGNORECASE)
        if not match:
            if words[0] == 'show':
                return 'help', self.help_show_columns()
        else:
            tablename = match.group('btable')
            column_list = match.group('columnlist')
            return 'show_columns', dict(tablename=tablename, column_list=column_list)
            
    def help_estimate_columns(self):
        return "ESTIMATE COLUMNS FROM <btable> [WHERE <whereclause>] [ORDER BY <orderable>] [LIMIT <limit>] [AS <column_list>]"

    def parse_estimate_columns(self, words, orig):
        ## TODO: add "as <name>". could use pyparsing.
        match = re.search(r"""
            estimate\s+columns\s+from\s+
            (?P<btable>[^\s]+)\s*
            (where\s+(?P<whereclause>.*?((?=limit)|(?=order)|(?=as)|$)))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'estimate' and words[2] == 'columns':
                return 'help', self.help_estimate_columns()
        else:
            tablename = match.group('btable').strip()
            whereclause = match.group('whereclause')
            if whereclause is None:
                whereclause = ''
            else:
                whereclause = whereclause.strip()
            limit = self.extract_limit(orig)                
            orig, order_by = self.extract_order_by(orig)
            name_match = re.search(r"""
              as\s+
              (?P<name>[^\s]+)
              \s*$
            """, orig, flags=re.VERBOSE|re.IGNORECASE)
            if name_match:
                name = name_match.group('name')
            else:
                name = None
            return 'estimate_columns', dict(tablename=tablename, whereclause=whereclause, limit=limit,
                                            order_by=order_by, name=name)
            
    def help_estimate_pairwise(self):
        return "ESTIMATE PAIRWISE [DEPENDENCE PROBABILITY | CORRELATION | MUTUAL INFORMATION] FROM <btable> [FOR <columns>] [SAVE TO <file>]: estimate a pairwise function of columns."
        
    def parse_estimate_pairwise(self, words, orig):
        match = re.search(r"""
            estimate\s+pairwise\s+
            (?P<functionname>.*?((?=\sfrom)))
            \s*from\s+
            (?P<btable>[^\s]+)
            (\s+for\s+columns\s+(?P<columns>[^\s]+))?
            (\s+save\s+to\s+(?P<filename>[^\s]+))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'estimate' and words[1] == 'pairwise':
                return 'help', self.help_estimate_pairwise()
        else:
            tablename = match.group('btable').strip()
            function_name = match.group('functionname').strip().lower()
            if function_name not in ["mutual information", "correlation", "dependence probability"]:
                return 'help', self.help_estimate_pairwise()
            if match.group('filename'):
                filename = match.group('filename')
            else:
                filename = None
            if match.group('columns'):
                column_list = match.group('columns')
            else:
                column_list = None
            return 'estimate_pairwise', dict(tablename=tablename, function_name=function_name,
                                             column_list=column_list), dict(filename=filename)


            
    def help_update_schema(self):
        return "UPDATE SCHEMA FOR <btable> SET (col0=numerical|categorical|key|ignore)[,...]: must be done before creating models or analyzing."
        
    def parse_update_schema(self, words, orig):
        match = re.search(r"""
            update\s+schema\s+for\s+
            (?P<btable>[^\s]+)\s+
            set\s+(?P<mappings>[^;]*);?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'update':
                return 'help', self.help_update_schema()
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
                elif 'key' in vals[1]:
                    datatype = 'key'
                elif 'ignore' in vals[1]:
                    datatype = 'ignore'
                else:
                    return 'help', self.help_update_datatypes()
                mappings[vals[0]] = datatype
            return 'update_schema', dict(tablename=tablename, mappings=mappings)

############################################################
# Parsing helper functions: "extract" functions
############################################################

    def extract_columns(self, orig):
        """TODO"""
        pattern = r"""
            \(\s*
            (estimate\s+)?
            columns\s+where\s+
            (?P<columnstring>\d+
            \)
        """
        match = re.search(pattern, orig.lower(), re.VERBOSE | re.IGNORECASE)
        if match:
            limit = int(match.group('limit').strip())
            return limit
        else:
            return float('inf')


    def extract_order_by(self, orig):
        pattern = r"""
            (order\s+by\s+(?P<orderbyclause>.*?((?=limit)|$)))
        """ 
        match = re.search(pattern, orig, re.VERBOSE | re.IGNORECASE)
        if match:
            order_by_clause = match.group('orderbyclause')
            ret = list()
            orderables = list()
            
            for orderable in utils.column_string_splitter(order_by_clause):
                ## Check for DESC/ASC
                desc = re.search(r'\s+(desc|asc)($|\s|,|(?=limit))', orderable, re.IGNORECASE)
                if desc is not None and desc.group().strip().lower() == 'desc':
                    desc = True
                else:
                    desc = False
                orderable = re.sub(r'\s+(desc|asc)($|\s|,|(?=limit))', '', orderable, flags=re.IGNORECASE)
                orderables.append((orderable.strip(), desc))
                
            orig = re.sub(pattern, '', orig, flags=re.VERBOSE | re.IGNORECASE)
            return (orig, orderables)
        else:
            return (orig, False)

            
    def extract_limit(self, orig):
        pattern = r'limit\s+(?P<limit>\d+)'
        match = re.search(pattern, orig.lower())
        if match:
            limit = int(match.group('limit').strip())
            return limit
        else:
            return float('inf')



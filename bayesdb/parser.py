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
        self.method_names = [method_name[6:] for method_name in dir(Parser) if method_name[:6] == 'parse_']
        self.method_names.remove('statement')
        self.method_name_to_args = be.get_method_name_to_args()
        self.reset_root_dir()
    
    def split_lines(self, bql_string):
        """
        Accepts a large chunk of BQL (such as a file containing many BQL statements)
        as a string, and returns individual BQL statements as a list of strings.

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
                return 'list_btables', dict(), None


    def help_execute_file(self):
        return "EXECUTE FILE <filename>: execute a BQL script from file."

    def parse_execute_file(self, words, orig):
        if len(words) >= 1 and words[0] == 'execute':
            if len(words) >= 3 and words[1] == 'file':
                filename = words[2]
                return 'execute_file', dict(filename=self.get_absolute_path(filename)), None
            else:
                return 'help', self.help_execute_file()

                
    def help_show_schema(self):
        return "SHOW SCHEMA FOR <btable>: show the datatype schema for the btable."

    def parse_show_schema(self, words, orig):
        if len(words) >= 4 and words[0] == 'show' and words[1] == 'schema':
            if words[2] == 'for':
                return 'show_schema', dict(tablename=words[3]), None
            else:
                return 'help', self.help_show_schema()

                
    def help_show_models(self):
        return "SHOW MODELS FOR <btable>: show the models and iterations stored for btable."

    def parse_show_models(self, words, orig):
        if len(words) >= 4 and words[0] == 'show' and words[1] == 'models':
            if words[2] == 'for':
                return 'show_models', dict(tablename=words[3]), None
            else:
                return 'help', self.help_show_models()

                
    def help_show_diagnostics(self):
        return "SHOW DIAGNOSTICS FOR <btable>: show diagnostics for this btable's models."

    def parse_show_diagnostics(self, words, orig):
        if len(words) >= 4 and words[0] == 'show' and words[1] == 'diagnostics':
            if words[2] == 'for':
                return 'show_diagnostics', dict(tablename=words[3]), None
            else:
                return 'help', self.help_show_diagnostics()


    def help_drop_models(self):
        return "DROP MODEL[S] [<id>-<id>] FROM <btable>: drop the models specified by the given ids."

    def parse_drop_models(self, words, orig):
        match = re.search(r"""
            drop\s+model(s)?\s+
            ( ((?P<start>\d+)\s*-\s*(?P<end>\d+)) | (?P<id>\d+) )?
            \s*(from|for)\s+
            (?P<btable>[^\s]+)
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'drop':
                return 'help', self.help_drop_models()
        else:
            tablename = match.group('btable')
            
            model_indices = None            
            start = match.group('start')
            end = match.group('end')
            if start is not None and end is not None:
                model_indices = range(int(start), int(end)+1)
            id = match.group('id')
            if id is not None:
                model_indices = [int(id)]
            
            return 'drop_models', dict(tablename=tablename, model_indices=model_indices), None
                
                
    def help_initialize_models(self):
        return "INITIALIZE <num_models> MODELS FOR <btable> [WITH CONFIG <model_config>]: the step to perform before analyze."

    def parse_initialize_models(self, words, orig):
        match = re.search(r"""
            initialize\s+
            (?P<num_models>[^\s]+)
            \s+model(s)?\s+for\s+
            (?P<btable>[^\s]+)
            (\s+with\s+config\s+(?P<model_config>.*))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'initialize' or (words[0] == 'create' and len(words) >= 2 and words[1] != 'models'):
                return 'help', self.help_initialize_models()
        else:
            n_models = int(match.group('num_models'))
            tablename = match.group('btable')
            model_config = match.group('model_config')

            if model_config is not None:
                model_config = model_config.strip()
            return 'initialize_models', dict(tablename=tablename, n_models=n_models,
                                             model_config=model_config), None
                    
    def help_create_btable(self):
        return "CREATE BTABLE <tablename> FROM <filename>: create a table from a csv file"

    def parse_create_btable(self, words, orig):
        crosscat_column_types = None
        if len(words) >= 2:
            if (words[0] == 'upload' or words[0] == 'create') and (words[1] == 'ptable' or words[1] == 'btable'):
                if len(words) >= 5:
                    tablename = words[2]
                    if words[3] == 'from':
                        csv_path = self.get_absolute_path(orig.split()[4])
                        return 'create_btable', \
                            dict(tablename=tablename, cctypes_full=crosscat_column_types), \
                            dict(csv_path=csv_path)
                    else:
                        return 'help', self.help_create_btable()
                else:
                    return 'help', self.help_create_btable()

                    
    def help_drop_btable(self):
        return "DROP BTABLE <tablename>: drop table."

    def parse_drop_btable(self, words, orig):
        if len(words) >= 3:
            if words[0] == 'drop' and (words[1] == 'tablename' or words[1] == 'ptable' or words[1] == 'btable'):
                return 'drop_btable', dict(tablename=words[2]), None


    def help_analyze(self):
        return "ANALYZE <btable> [MODEL[S] <id>-<id>] [FOR <iterations> ITERATIONS | FOR <seconds> SECONDS]: perform inference."

    def parse_analyze(self, words, orig):
        match = re.search(r"""
            analyze\s+
            (?P<btable>[^\s]+)\s+
            (model(s)?\s+
              (((?P<start>\d+)\s*-\s*(?P<end>\d+)) | (?P<id>\d+)) )?
            \s*for\s+
            ((?P<iterations>\d+)\s+iteration(s)?)?
            ((?P<seconds>\d+)\s+second(s)?)?
            (\s*with\s+(?P<kernel>[^\s]+)\s+kernel)?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None or (match.group('iterations') is None and match.group('seconds') is None):
            if words[0] == 'analyze':
                return 'help', self.help_analyze()
        else:
            model_indices = None
            tablename = match.group('btable')

            start = match.group('start')
            end = match.group('end')
            if start is not None and end is not None:
                model_indices = range(int(start), int(end)+1)
            id = match.group('id')
            if id is not None:
                model_indices = [int(id)]
            
            iterations = match.group('iterations')
            if iterations is not None:
                iterations = int(iterations)
            
            seconds = match.group('seconds')
            if seconds is not None:
                seconds = int(seconds)

            kernel = match.group('kernel')
            if kernel is not None and kernel.strip().lower()=='mh':
                ct_kernel = 1
            else:
                ct_kernel = 0
                
            return 'analyze', dict(tablename=tablename, model_indices=model_indices,
                                   iterations=iterations, seconds=seconds, ct_kernel=ct_kernel), None

            
    def help_infer(self):
        return "[SUMMARIZE] INFER [HIST|SCATTER [PAIRWISE]] <columns|functions> FROM <btable> [WHERE <whereclause>] [WITH CONFIDENCE <confidence>] [WITH <numsamples> SAMPLES] [ORDER BY <columns|functions>] [LIMIT <limit>] [USING MODEL[S] <id>-<id>] [SAVE TO <file>]: like select, but imputes (fills in) missing values."
        
    def parse_infer(self, words, orig):
        match = re.search(r"""
            ((?P<summarize>summarize)?)?\s*
            infer\s+
            ((?P<plot>(hist|scatter))(?P<pairwise>\s+pairwise)?)?\s*
            (?P<columnstring>[^\s,]+(?:,\s*[^\s,]+)*)\s+
            from\s+(?P<btable>[^\s]+)\s+
            (where\s+(?P<whereclause>.*(?=with)))?
            \s*with\s+confidence\s+(?P<confidence>[^\s]+)
            (\s+limit\s+(?P<limit>\d+))?
            (\s+with\s+(?P<numsamples>[^\s]+)\s+samples)?
            (\s*save\s+to\s+(?P<filename>[^\s]+))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'infer':
                return 'help', self.help_infer()
        else:
            summarize = match.group('summarize') is not None
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
                numsamples = None
            else:
                numsamples = int(numsamples)
            newtablename = '' # For INTO
            orig, order_by = self.extract_order_by(orig)
            modelids = self.extract_using_models(orig)

            plot = match.group('plot') is not None
            if plot:
                scatter = 'scatter' in match.group('plot')
                pairwise = match.group('pairwise') is not None
            else:
                scatter = False
                pairwise = False                
                
            if match.group('filename'):
                filename = match.group('filename')
            else:
                filename = None
            return 'infer', \
                   dict(tablename=tablename, columnstring=columnstring, newtablename=newtablename,
                        confidence=confidence, whereclause=whereclause, limit=limit,
                        numsamples=numsamples, order_by=order_by, plot=plot, modelids=modelids, summarize=summarize), \
                   dict(plot=plot, scatter=scatter, pairwise=pairwise, filename=filename)

            
            
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
            pkl_path = match.group('pklpath')
            return 'save_models', dict(tablename=tablename), dict(pkl_path=pkl_path)


            
    def help_load_models(self):
        return "LOAD MODELS <pklpath> INTO <btable>: load models from a pickle file."
        
    def parse_load_models(self, words, orig):
        match = re.search(r"""
            load\s+
            models\s+
            (?P<pklpath>[^\s]+)\s+
            ((into\s+)|(for\s+))
            (?P<btable>[^\s]+)\s*$
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'load':
                return 'help', self.help_load_models()
        else:
            tablename = match.group('btable')
            pkl_path = match.group('pklpath')
            return 'load_models', dict(tablename=tablename), dict(pkl_path=pkl_path)


            
    def help_select(self):
        return '[SUMMARIZE] SELECT [HIST|SCATTER [PAIRWISE]] <columns|functions> FROM <btable> [WHERE <whereclause>] [ORDER BY <columns|functions>] [LIMIT <limit>] [USING MODEL[S] <id>-<id>] [SAVE TO <filename>]'
        
    def parse_select(self, words, orig):
        match = re.search(r"""
            ((?P<summarize>summarize)?)?\s*        
            select\s+
            ((?P<plot>(hist|scatter))(?P<pairwise>\s+pairwise)?)?\s*      
            (?P<columnstring>.*?((?=from)))
            \s*from\s+(?P<btable>[^\s]+)\s*
            (where\s+(?P<whereclause>.*?((?=limit)|(?=order)|$)))?
            (\s*limit\s+(?P<limit>\d+))?
            (\s*save\s+to\s+(?P<filename>[^\s]+))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'select':
                return 'help', self.help_select()
        else:
            summarize = match.group('summarize') is not None
            columnstring = match.group('columnstring').strip()
            tablename = match.group('btable')
            whereclause = match.group('whereclause')
            if whereclause is None:
                whereclause = ''
            else:
                whereclause = whereclause.strip()
            limit = self.extract_limit(orig)
            orig, order_by = self.extract_order_by(orig)
            modelids = self.extract_using_models(orig)

            plot = match.group('plot') is not None
            if plot:
                scatter = 'scatter' in match.group('plot')
                pairwise = match.group('pairwise') is not None
            else:
                scatter = False
                pairwise = False

            if match.group('filename'):
                filename = match.group('filename')
            else:
                filename = None

            return 'select', dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
                                  limit=limit, order_by=order_by, plot=plot, modelids=modelids, summarize=summarize), \
              dict(pairwise=pairwise, scatter=scatter, filename=filename, plot=plot)


    def help_simulate(self):
        return "[SUMMARIZE] SIMULATE [HIST|SCATTER [PAIRWISE]] <columns> FROM <btable> [WHERE <whereclause>] TIMES <times> [USING MODEL[S] <id>-<id>] [SAVE TO <filename>]: simulate new datapoints based on the underlying model."

    def parse_simulate(self, words, orig):
        match = re.search(r"""
            ((?P<summarize>summarize)?)?\s*        
            simulate\s+
            ((?P<plot>(hist|scatter))(?P<pairwise>\s+pairwise)?)?\s*
            (?P<columnstring>[^\s,]+(?:,\s*[^\s,]+)*)\s+
            from\s+(?P<btable>[^\s]+)\s+
            ((given|where)\s+(?P<givens>.*(?=times)))?
            times\s+(?P<times>\d+)
            (\s*save\s+to\s+(?P<filename>[^\s]+))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'simulate':
                return 'help', self.help_simulate()
        else:
            summarize = match.group('summarize') is not None
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
            modelids = self.extract_using_models(orig)
            
            plot = match.group('plot') is not None
            if plot:
                scatter = 'scatter' in match.group('plot')
                pairwise = match.group('pairwise') is not None
            else:
                scatter = False
                pairwise = False
            
            if match.group('filename'):
                filename = match.group('filename')
            else:
                filename = None            
            return 'simulate', \
                    dict(tablename=tablename, columnstring=columnstring, newtablename=newtablename,
                         givens=givens, numpredictions=numpredictions, order_by=order_by, plot=plot, modelids=modelids, summarize=summarize), \
                    dict(filename=filename, plot=plot, scatter=scatter, pairwise=pairwise)

    def help_show_row_lists(self):
        return "SHOW ROW LISTS FOR <btable>"

    def parse_show_row_lists(self, words, orig):
        match = re.search(r"""
          SHOW\s+ROW\s+LISTS\s+FOR\s+
          (?P<btable>[^\s]+)\s*$
        """, orig, flags=re.VERBOSE|re.IGNORECASE)
        if not match:
            if words[0] == 'show':
                return 'help', self.help_show_row_lists()
        else:
            tablename = match.group('btable')
            return 'show_row_lists', dict(tablename=tablename), None

    def help_show_column_lists(self):
        return "SHOW COLUMN LISTS FOR <btable>"

    def parse_show_column_lists(self, words, orig):
        match = re.search(r"""
          SHOW\s+COLUMN\s+LISTS\s+FOR\s+
          (?P<btable>[^\s]+)\s*$
        """, orig, flags=re.VERBOSE|re.IGNORECASE)
        if not match:
            if words[0] == 'show':
                return 'help', self.help_show_column_lists()
        else:
            tablename = match.group('btable')
            return 'show_column_lists', dict(tablename=tablename), None

    def help_show_columns(self):
        return "SHOW COLUMNS <column_list> FROM <btable>"

    def parse_show_columns(self, words, orig):
        match = re.search(r"""
          SHOW\s+COLUMNS\s+
          ((?P<columnlist>[^\s]+)\s+)?
          FROM\s+
          (?P<btable>[^\s]+)\s*$
        """, orig, flags= re.VERBOSE | re.IGNORECASE)
        if not match:
            if words[0] == 'show':
                return 'help', self.help_show_columns()
        else:
            tablename = match.group('btable')
            column_list = match.group('columnlist')
            return 'show_columns', dict(tablename=tablename, column_list=column_list), None

            
    def help_estimate_columns(self):
        return "(ESTIMATE COLUMNS | CREATE COLUMN LIST) [<column_names>] FROM <btable> [WHERE <whereclause>] [ORDER BY <orderable>] [LIMIT <limit>] [USING MODEL[S] <id>-<id>] [AS <column_list>]"

    def parse_estimate_columns(self, words, orig):
        match = re.search(r"""
            ((estimate\s+columns\s+)|(create\s+column\s+list\s+))
            (?P<columnstring>.*?((?=from)))
            \s*from\s+
            (?P<btable>[^\s]+)\s*
            (where\s+(?P<whereclause>.*?((?=limit)|(?=order)|(?=as)|$)))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if (words[0] == 'estimate' and words[2] == 'columns') or (words[0] == 'create' and words[1] == 'column'):
                return 'help', self.help_estimate_columns()
        else:
            tablename = match.group('btable').strip()
            
            columnstring = match.group('columnstring')
            if columnstring is None:
                columnstring = ''
            else:
                columnstring = columnstring.strip()
                
            whereclause = match.group('whereclause')
            if whereclause is None:
                whereclause = ''
            else:
                whereclause = whereclause.strip()
                
            limit = self.extract_limit(orig)                
            orig, order_by = self.extract_order_by(orig)
            modelids = self.extract_using_models(orig)            
            
            name_match = re.search(r"""
              as\s+
              (?P<name>[^\s]+)
              \s*$
            """, orig, flags=re.VERBOSE|re.IGNORECASE)
            if name_match:
                name = name_match.group('name')
            else:
                name = None

            return 'estimate_columns', dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
                                            limit=limit, order_by=order_by, name=name, modelids=modelids), None

    def help_estimate_pairwise_row(self):
        return "ESTIMATE PAIRWISE ROW SIMILARITY FROM <btable> [FOR <rows>] [USING MODEL[S] <id>-<id>] [SAVE TO <file>] [SAVE CONNECTED COMPONENTS WITH THRESHOLD <threshold> [INTO|AS] <btable>]: estimate a pairwise function of columns."

    def parse_estimate_pairwise_row(self, words, orig):
        match = re.search(r"""
            estimate\s+pairwise\s+row\s+
            (?P<functionname>.*?((?=\sfrom)))
            \s*from\s+
            (?P<btable>[^\s]+)
            (\s+for\s+rows\s+(?P<rows>[^\s]+))?
            (\s+save\s+to\s+(?P<filename>[^\s]+))?
            (\s+save\s+connected\s+components\s+with\s+threshold\s+(?P<threshold>[^\s]+)\s+(as|into)\s+(?P<components_name>[^\s]+))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'estimate' and words[1] == 'pairwise':
                return 'help', self.help_estimate_pairwise()
        else:
            tablename = match.group('btable').strip()
            function_name = match.group('functionname')
            if function_name.strip().lower().split()[0] not in ["similarity"]:
                return 'help', self.help_estimate_pairwise()
            filename = match.group('filename') # Could be None
            row_list = match.group('rows') # Could be None
            if match.group('components_name') and match.group('threshold'):
                components_name = match.group('components_name')
                threshold = float(match.group('threshold'))
            else:
                components_name = None
                threshold = None
            modelids = self.extract_using_models(orig)                            
            return 'estimate_pairwise_row', \
              dict(tablename=tablename, function_name=function_name,
                   row_list=row_list, components_name=components_name, threshold=threshold, modelids=modelids), \
              dict(filename=filename)

        
    def help_estimate_pairwise(self):
        return "ESTIMATE PAIRWISE [DEPENDENCE PROBABILITY | CORRELATION | MUTUAL INFORMATION] FROM <btable> [FOR <columns>] [USING MODEL[S] <id>-<id>] [SAVE TO <file>] [SAVE CONNECTED COMPONENTS WITH THRESHOLD <threshold> AS <columnlist>]: estimate a pairwise function of columns."
        
    def parse_estimate_pairwise(self, words, orig):
        match = re.search(r"""
            estimate\s+pairwise\s+
            (?P<functionname>.*?((?=\sfrom)))
            \s*from\s+
            (?P<btable>[^\s]+)
            (\s+for\s+columns\s+(?P<columns>[^\s]+))?
            (\s+save\s+to\s+(?P<filename>[^\s]+))?
            (\s+save\s+connected\s+components\s+with\s+threshold\s+(?P<threshold>[^\s]+)\s+as\s+(?P<components_name>[^\s]+))?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'estimate' and words[1] == 'pairwise':
                return 'help', self.help_estimate_pairwise()
        else:
            tablename = match.group('btable').strip()
            function_name = match.group('functionname').strip().lower()
            if function_name not in ["mutual information", "correlation", "dependence probability"]:
                return 'help', self.help_estimate_pairwise()
            filename = match.group('filename') # Could be None
            column_list = match.group('columns') # Could be None
            if match.group('components_name') and match.group('threshold'):
                components_name = match.group('components_name')
                threshold = float(match.group('threshold'))
            else:
                components_name = None
                threshold = None
            modelids = self.extract_using_models(orig)                            
            return 'estimate_pairwise', \
              dict(tablename=tablename, function_name=function_name,
                   column_list=column_list, components_name=components_name, threshold=threshold, modelids=modelids), \
              dict(filename=filename)

    def help_label_columns(self):
        return "LABEL COLUMNS FOR <btable> [<column1>=value1[,...]]: "

    def parse_label_columns(self, words, orig):
        match = re.search(r"""
            label\s+columns\s+for\s+
            (?P<btable>[^\s]+)\s+
            (?P<mappings>[^;]*);?
        """, orig, re.VERBOSE | re.IGNORECASE)
        if match is None:
            if words[0] == 'label':
                return 'help', self.help_label_columns()
        else:
            tablename = match.group('btable').strip()
            mapping_string = match.group('mappings').strip()
            mappings = dict()
            for mapping in mapping_string.split(','):
                vals = mapping.split('=')
                column, label = vals[0].strip(), vals[1].strip()
                mappings[column.strip()] = label
            return 'label_columns', dict(tablename=tablename, mappings=mappings), None
            
    def help_update_schema(self):
        return "UPDATE SCHEMA FOR <btable> SET [<column_name>=(numerical|categorical|key|ignore)[,...]]: must be done before creating models or analyzing."
        
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
                mappings[vals[0].strip()] = datatype
            return 'update_schema', dict(tablename=tablename, mappings=mappings), None

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

    def extract_using_models(self, orig):
        """
        """
        match = re.search(r"""
            (model(s)?\s+
              (((?P<start>\d+)\s*-\s*(?P<end>\d+)) | (?P<id>\d+)) )?
        """, orig, flags = re.VERBOSE | re.IGNORECASE)
        if match:
            modelids = None
            start = match.group('start')
            end = match.group('end')
            if start is not None and end is not None:
                modelids = range(int(start), int(end)+1)
            id = match.group('id')
            if id is not None:
                modelids = [int(id)]
            return modelids


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



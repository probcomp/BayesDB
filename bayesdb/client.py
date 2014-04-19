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

import inspect
import pickle
import gzip
import prettytable
import re
import os
import time
import ast

import utils
import data_utils
import plotting_utils
import api_utils
from parser import Parser
from engine import Engine

class Client(object):
    def __init__(self, crosscat_host=None, crosscat_port=8007, crosscat_engine_type='multiprocessing',
                 bayesdb_host=None, bayesdb_port=8008, seed=None):
        """
        Create a client object. The client creates a parser, that is uses to parse all commands,
        and an engine, which is uses to execute all commands. The engine can be remote or local.
        If local, the engine will be created.
        """
        self.parser = Parser()
        if bayesdb_host is None or bayesdb_host=='localhost':
            self.online = False
            self.engine = Engine(crosscat_host, crosscat_port, crosscat_engine_type, seed)
        else:
            self.online = True
            self.hostname = bayesdb_host
            self.port = bayesdb_port
            self.URI = 'http://' + self.hostname + ':%d' % self.port

    def call_bayesdb_engine(self, method_name, args_dict, debug=False):
        """
        Helper function used to call the BayesDB engine, whether it is remote or local.
        Accepts method name and arguments for that method as input.
        """
        if self.online:
            out, id = aqupi_utils.call(method_name, args_dict, self.URI)
        else:
            method = getattr(self.engine, method_name)
            if debug:
                out = method(**args_dict)
            else:
                # when not in debug mode, catch all BayesDBErrors
                try:
                    out = method(**args_dict)
                except utils.BayesDBError as e:
                    out = dict(message=str(e), error=True)
        return out

    def __call__(self, call_input, pretty=True, timing=False, wait=False, plots=None, yes=False, debug=False, pandas_df=None, pandas_output=True):
        """Wrapper around execute."""
        return self.execute(call_input, pretty, timing, wait, plots, yes, debug, pandas_df, pandas_output)

    def execute(self, call_input, pretty=True, timing=False, wait=False, plots=None, yes=False, debug=False, pandas_df=None, pandas_output=True):
        """
        Execute a chunk of BQL. This method breaks a large chunk of BQL (like a file)
        consisting of possibly many BQL statements, breaks them up into individual statements,
        then passes each individual line to self.execute_statement() as a string.
        
        param call_input: may be either a file object, or a string.
        If the input is a file, then we load the inputs of the file, and use those as a string.

        See self.execute_statement() for an explanation of arguments.
        """
        if type(call_input) == file:
            bql_string = call_input.read()
            path = os.path.abspath(call_input.name)
            self.parser.set_root_dir(os.path.dirname(path))
        elif type(call_input) == str:
            bql_string = call_input
        else:
            print "Invalid input type: expected file or string."

        return_list = []
            
        lines = self.parser.split_lines(bql_string)
        # Iterate through lines with while loop so we can append within loop.
        while len(lines) > 0:
            line = lines.pop(0)
            if type(call_input) == file:
                print '> %s' % line
            if wait:
                user_input = raw_input()
                if len(user_input) > 0 and (user_input[0] == 'q' or user_input[0] == 's'):
                    continue
            result = self.execute_statement(line, pretty=pretty, timing=timing, plots=plots, yes=yes, debug=debug, pandas_df=pandas_df, pandas_output=pandas_output)

            if type(result) == dict and 'message' in result and result['message'] == 'execute_file':
                ## special case for one command: execute_file
                new_lines = self.parser.split_lines(result['bql_string'])
                lines += new_lines
            if type(call_input) == file:
                print

            return_list.append(result)

        self.parser.reset_root_dir()

        if not pretty:
            return return_list

    def execute_statement(self, bql_statement_string, pretty=True, timing=False, plots=None, yes=False, debug=False, pandas_df=None, pandas_output=True):
        """
        Accepts a SINGLE BQL STATEMENT as input, parses it, and executes it if it was parsed
        successfully.

        If pretty=True, then the command output will be pretty-printed as a string.
        If pretty=False, then the command output will be returned as a python object.

        timing=True prints out how long the command took to execute.

        For commands that have visual results, plots=True will cause those to be displayed
        by matplotlib as graphics rather than being pretty-printed as text.
        (Note that the graphics will also be saved if the user added SAVE TO <filename> to the BQL.)
        """
        if timing:
            start_time = time.time()

        try:
            parser_out  = self.parser.parse_statement(bql_statement_string)
        except Exception as e:
            raise utils.BayesDBParseError(str(e))
        if parser_out is None:
            print "Could not parse command. Try typing 'help' for a list of all commands."
            return
        elif not parser_out:
            return

        method_name, args_dict, client_dict = parser_out
        if client_dict is None:
            client_dict = {}
            
        ## Do stuff now that you know the user's command, but before passing it to engine.
        if method_name == 'execute_file':
            return dict(message='execute_file', bql_string=open(args_dict['filename'], 'r').read())
        elif (method_name == 'drop_btable') and (not yes):
            ## If dropping something, ask for confirmation.
            print "Are you sure you want to permanently delete this btable, and all associated models, without any way to get them back? Enter 'y' if yes."
            user_confirmation = raw_input()
            if 'y' != user_confirmation.strip():
                return dict(message="Operation canceled by user.")
        elif (method_name == 'drop_models') and (not yes):
            ## If dropping something, ask for confirmation.
            print "Are you sure you want to permanently delete model(s), without any way to get them back? Enter 'y' if yes."
            user_confirmation = raw_input()
            if 'y' != user_confirmation.strip():
                return dict(message="Operation canceled by user.")
        elif method_name == 'load_models':
            pklpath = client_dict['pkl_path']
            try:
                models = pickle.load(gzip.open(self.parser.get_absolute_path(pklpath), 'rb'))
            except IOError as e:
                if pklpath[-7:] != '.pkl.gz':
                    if pklpath[-4:] == '.pkl':
                        models = pickle.load(open(self.parser.get_absolute_path(pklpath), 'rb'))
                    else:
                        pklpath = pklpath + ".pkl.gz"
                        models = pickle.load(gzip.open(self.parser.get_absolute_path(pklpath), 'rb'))
                else:
                    raise utils.BayesDBError('Models file %s could not be found.' % pklpath)
            args_dict['models'] = models
        elif method_name == 'create_btable':
            if pandas_df is None:
                header, rows = data_utils.read_csv(client_dict['csv_path'])
            else:
                header, rows = data_utils.read_pandas_df(pandas_df)
            args_dict['header'] = header
            args_dict['raw_T_full'] = rows
        elif method_name in ['label_columns', 'update_metadata']:
            if client_dict['source'] == 'file':
                header, rows = data_utils.read_csv(client_dict['csv_path'])
                args_dict['mappings'] = {key: value for key, value in rows}

        ## Call engine.
        result = self.call_bayesdb_engine(method_name, args_dict, debug)

        ## If error occurred, exit now.
        if 'error' in result and result['error']:
            if pretty:
                print result['message']
                return result['message']
            else:
                return result

        ## Do stuff now that engine has given you output, but before printing the result.
        result = self.callback(method_name, args_dict, client_dict, result)
        
        assert type(result) != int
        
        if timing:
            end_time = time.time()
            print 'Elapsed time: %.2f seconds.' % (end_time - start_time)

        if plots is None:
            plots = 'DISPLAY' in os.environ.keys()

        if 'matrix' in result and (plots or client_dict['filename']):
            # Plot matrices
            plotting_utils.plot_matrix(result['matrix'], result['column_names'], result['title'], client_dict['filename'])
            if pretty:
                if 'column_lists' in result:
                    print self.pretty_print(dict(column_lists=result['column_lists']))
                return self.pretty_print(result)
            else:
                return result
        if ('plot' in client_dict and client_dict['plot']):
            if (plots or client_dict['filename']):
                # Plot generalized histograms or scatterplots
                plotting_utils.plot_general_histogram(result['columns'], result['data'], result['M_c'], client_dict['filename'], client_dict['scatter'], client_dict['pairwise'])
                return self.pretty_print(result)
            else:
                if 'message' not in result:
                    result['message'] = ""
                result['message'] = "Your query indicates that you would like to make a plot, but in order to do so, you must either enable plotting in a window or specify a filename to save to by appending 'SAVE TO <filename>' to this command.\n" + result['message']

        if pretty:
            pp = self.pretty_print(result)
            print pp
        
        if pandas_output and 'data' in result and 'columns' in result:
            result_pandas_df = data_utils.construct_pandas_df(result)
            return result_pandas_df
        else:
            if type(result) == dict and 'message' in result.keys():
                print result['message']
            return result

    def callback(self, method_name, args_dict, client_dict, result):
        """
        This method is meant to be called after receiving the result of a
        call to the BayesDB engine, and modifies the output before it is displayed
        to the user.
        """
        if method_name == 'save_models':
            samples_dict = result
            ## Here is where the models get saved.
            pkl_path = client_dict['pkl_path']
            if pkl_path[-7:] != '.pkl.gz':
                if pkl_path[-4:] == '.pkl':
                    pkl_path = pkl_path + ".gz"
                else:
                    pkl_path = pkl_path + ".pkl.gz"
            samples_file = gzip.GzipFile(pkl_path, 'w')
            pickle.dump(samples_dict, samples_file)
            return dict(message="Successfully saved the samples to %s" % client_dict['pkl_path'])

        else:
            return result
        
    def pretty_print(self, query_obj):
        """
        Return a pretty string representing the output object.
        """
        assert type(query_obj) == dict
        result = ""
        if type(query_obj) == dict and 'message' in query_obj:
            result += query_obj["message"] + "\n"
        if 'data' in query_obj and 'columns' in query_obj:
            """ Pretty-print data table """
            pt = prettytable.PrettyTable()
            pt.field_names = query_obj['columns']
            for row in query_obj['data']:
                pt.add_row(row)
            result += str(pt)
        elif 'list' in query_obj:
            """ Pretty-print lists """
            result += str(query_obj['list'])
        elif 'column_names' in query_obj:
            """ Pretty-print cctypes """
            colnames = query_obj['column_names']
            zmatrix = query_obj['matrix']
            pt = prettytable.PrettyTable(hrules=prettytable.ALL, vrules=prettytable.ALL, header=False)
            pt.add_row([''] + list(colnames))
            for row, colname in zip(zmatrix, list(colnames)):
                pt.add_row([colname] + list(row))
            result += str(pt)
        elif 'columns' in query_obj:
            """ Pretty-print column list."""
            pt = prettytable.PrettyTable()
            pt.field_names = query_obj['columns']
            result += str(pt)
        elif 'row_lists' in query_obj:
            """ Pretty-print multiple row lists, which are just names and row sizes. """
            pt = prettytable.PrettyTable()
            pt.field_names = ('Row List Name', 'Row Count')
            
            def get_row_list_sorting_key(x):
                """ To be used as the key function in a sort. Puts cc_2 ahead of cc_10, e.g. """
                name, count = x
                if '_' not in name:
                    return name
                s = name.split('_')
                end = s[-1]
                start = '_'.join(s[:-1])
                if utils.is_int(end):
                    return (start, int(end))
                return name
                    
            for name, count in sorted(query_obj['row_lists'], key=get_row_list_sorting_key):
                pt.add_row((name, count))
            result += str(pt)
        elif 'column_lists' in query_obj:
            """ Pretty-print multiple column lists. """
            print
            clists = query_obj['column_lists']
            for name, clist in clists:
                print "%s:" % name
                pt = prettytable.PrettyTable()
                pt.field_names = clist
                print pt
        elif 'models' in query_obj:
            """ Pretty-print model info. """
            m = query_obj['models']
            output_list = ['Model %d: %d iterations' % (id, iterations) for id,iterations in m]
            result += ', '.join(output_list)

        if len(result) >= 1 and result[-1] == '\n':
            result = result[:-1]
        return result




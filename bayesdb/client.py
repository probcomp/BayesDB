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
from textwrap import dedent

import utils
import data_utils
import plotting_utils
import api_utils
from parser import Parser
from engine import Engine


class Client(object):
    def __init__(self, crosscat_host=None, crosscat_port=8007,
                 crosscat_engine_type='multiprocessing', bayesdb_host=None, bayesdb_port=8008,
                 seed=None, testing=False):
        """
        Create a client object. The client creates a parser, that is uses to parse all commands,
        and an engine, which is uses to execute all commands. The engine can be remote or local.
        If local, the engine will be created.
        """
        self.parser = Parser()
        if bayesdb_host is None or bayesdb_host == 'localhost':
            self.online = False
            self.engine = Engine(crosscat_host, crosscat_port, crosscat_engine_type, seed,
                                 testing=testing)
        else:
            self.online = True
            self.hostname = bayesdb_host
            self.port = bayesdb_port
            self.URI = 'http://' + self.hostname + ':%d' % self.port

    def call_bayesdb_engine(self, method_name, args_dict, debug=False):
        """
        Helper function used to call the BayesDB engine, whether it is remote or local.
        Accepts method name and arguments for that method as input.
        If this is the first time a query has been executed on the given tablename
        during this session, first check that the table doesn't need any upgrades to
        work with the current version of BayesDB. (After checking/upgrading, the table
        will be considered upgraded for the duration of the session.)
        """
        table_query = 'tablename' in args_dict
        if table_query:
            tablename = args_dict['tablename']
            if self.online:
                out, id = api_utils.call('check_btable_created_and_checked',
                                         {'tablename': tablename, 'client_online': True}, self.URI)
                table_created = out['result']['table_created']
                table_checked = out['result']['table_checked']
            else:
                table_created, table_checked = self.engine.check_btable_created_and_checked(tablename)
        if self.online:
            if table_query:
                if table_created and not table_checked and method_name is not 'drop_btable':
                    out, id = aqupi_utils.call('upgrade_btable', {'tablename': tablename}, self.URI)
            out, id = aqupi_utils.call(method_name, args_dict, self.URI)
        else:
            if table_query:
                if table_created and not table_checked and method_name is not 'drop_btable':
                    self.engine.upgrade_btable(tablename)
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

    def __call__(self, call_input, pretty=True, timing=False, wait=False, plots=None, yes=False,
                 debug=False, pandas_df=None, pandas_output=True, key_column=None,
                 return_raw_result=False, force_output=False):
        """Wrapper around execute."""
        return self.execute(call_input, pretty, timing, wait, plots, yes, debug, pandas_df,
                            pandas_output, key_column, return_raw_result, force_output)

    def execute(self, call_input, pretty=True, timing=False, wait=False, plots=None, yes=False,
                debug=False, pandas_df=None, pandas_output=True, key_column=None,
                return_raw_result=False, force_output=False):
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
            try:
                call_input.encode('ascii', 'ignore')
                bql_string = call_input
            except:
                raise ValueError("Invalid input type: expected file or string. Got: %s of type %s."
                                 % (call_input, type(call_input)))

        return_list = []

        # Parse input, but catch parsing errors and abort
        try:
            lines = [bql_statement_ast for bql_statement_ast in self.parser.pyparse_input(bql_string)]
        except utils.BayesDBError as e:
            if debug:
                raise e
            else:
                print(str(e))
                return

        # Iterate through lines with while loop so we can append within loop.
        while len(lines) > 0:
            line = lines.pop(0)
            if type(call_input) == file:
                print('> %s' % line)
            if wait:
                user_input = raw_input()
                if len(user_input) > 0 and (user_input[0] == 'q' or user_input[0] == 's'):
                    continue
            result = self.execute_statement(line, pretty=pretty, timing=timing, plots=plots,
                                            yes=yes, debug=debug, pandas_df=pandas_df,
                                            pandas_output=pandas_output, key_column=key_column,
                                            return_raw_result=return_raw_result,
                                            force_output=force_output)

            if type(result) == dict and 'message' in result and result['message'] == 'execute_file':
                # special case for one command: execute_file
                new_lines = self.parser.split_lines(result['bql_string'])
                lines += new_lines
            if type(call_input) == file:
                print

            return_list.append(result)

        self.parser.reset_root_dir()

        if not pretty or return_raw_result or force_output:
            return return_list

    def execute_statement(self, bql_statement_ast, pretty=True, timing=False, plots=None, yes=False,
                          debug=False, pandas_df=None, pandas_output=True, key_column=None,
                          return_raw_result=False, force_output=False):
        """
        Accepts a SINGLE BQL STATEMENT as input, parses it, and executes it if it was parsed
        successfully.

        If pretty=True, then the command output will be pretty-printed as a string.
        If pretty=False, then the command output will be returned as a python object.
        If force_output=True, then results will be returned regardless of pretty

        timing=True prints out how long the command took to execute.

        For commands that have visual results, plots=True will cause those to be displayed
        by matplotlib as graphics rather than being pretty-printed as text.
        (Note that the graphics will also be saved if the user added SAVE TO <filename> to the BQL.)
        """
        if timing:
            start_time = time.time()

        parser_out = None
        # TODO move pyparsing objects out of client into parser
        if debug:
            parser_out = self.parser.parse_single_statement(bql_statement_ast)
        else:
            try:
                parser_out = self.parser.parse_single_statement(bql_statement_ast)
            except Exception as e:
                raise utils.BayesDBParseError(str(e))
        if parser_out is None:
            print("Could not parse command. Try typing 'help' for a list of all commands.")
            return
        elif not parser_out:
            return

        method_name, args_dict, client_dict = parser_out
        if client_dict is None:
            client_dict = {}

        # Do stuff now that you know the user's command, but before passing it to engine.
        if method_name == 'execute_file':
            return dict(message='execute_file', bql_string=open(args_dict['filename'], 'r').read())
        elif method_name == 'update_codebook':
            _, codebook_rows = data_utils.read_csv(client_dict['codebook_path'], has_header=True)
            # TODO: require specific codebook_header values? Or don't require a header,
            # and if the first value in the header is actually a data column name, assume
            # the first row is codebook data, not a header.

            # Create a dict indexed by column name
            codebook = dict()
            for codebook_row in codebook_rows:
                codebook[codebook_row[0]] = dict(zip(['short_name', 'description', 'value_map'],
                                                 codebook_row[1:]))

            args_dict['codebook'] = codebook
        elif (method_name == 'drop_btable') and (not yes):
            # If dropping something, ask for confirmation.
            print("Are you sure you want to permanently delete this btable, and all associated "
                  "models, without any way to get them back? Enter 'y' if yes.")
            user_confirmation = raw_input()
            if 'y' != user_confirmation.strip():
                return dict(message="Operation canceled by user.")
        elif (method_name == 'drop_models') and (not yes):
            # If dropping something, ask for confirmation.
            print("Are you sure you want to permanently delete model(s), without any way to get "
                  "them back? Enter 'y' if yes.")
            user_confirmation = raw_input()
            if 'y' != user_confirmation.strip():
                return dict(message="Operation canceled by user.")
        elif method_name == 'load_models':
            pklpath = client_dict['pkl_path']
            try:
                model_data = pickle.load(gzip.open(self.parser.get_absolute_path(pklpath), 'rb'))
            except IOError as e:
                if pklpath[-7:] != '.pkl.gz':
                    if pklpath[-4:] == '.pkl':
                        model_data = pickle.load(open(self.parser.get_absolute_path(pklpath), 'rb'))
                    else:
                        pklpath = pklpath + ".pkl.gz"
                        model_data = pickle.load(gzip.open(self.parser.get_absolute_path(pklpath),
                                                 'rb'))
                else:
                    raise utils.BayesDBError('Models file %s could not be found.' % pklpath)
            # This is the more recent version, where schema is stored with models.
            if 'schema' in model_data.keys():
                args_dict['models'] = model_data['models']
                args_dict['model_schema'] = model_data['schema']
            # This support older saved models, where only the model info was stored.
            else:
                args_dict['models'] = model_data
                args_dict['model_schema'] = None

            # Older versions of model_schema just had a str cctype as the dict items.
            # Newest version has a dict of cctype and parameters. Use this values to
            # test the recency of the models.
            model_schema = args_dict['model_schema']
            if model_schema:
                model_schema_itemtype = type(model_schema[model_schema.keys()[0]])
            else:
                model_schema_itemtype = None

            if model_schema is None or model_schema_itemtype != dict:
                args_dict['model_schema'] = None
                if not yes:
                    print """WARNING! The models you are currently importing were saved without a schema
                        or without detailed column parameters (probably from a previous version).

                        If you are loading models into the same table from which you created them, problems
                        are unlikely, unless you have dropped models and then updated the schema.

                        If you are loading models into a different table from which you created them, you
                        should verify that the table schemas are the same.

                        Please use "SAVE MODELS FROM <btable> TO <filename.pkl.gz>" to create an updated copy of your models.

                        Are you sure you want to load these model(s)?
                        """
                    user_confirmation = raw_input()
                    if 'y' != user_confirmation.strip():
                        return dict(message="Operation canceled by user.")
        elif method_name == 'create_btable':
            if pandas_df is None:
                header, rows = data_utils.read_csv(client_dict['csv_path'])
            else:
                header, rows = data_utils.read_pandas_df(pandas_df)
            args_dict['header'] = header
            args_dict['raw_T_full'] = rows
            args_dict['key_column'] = key_column
            args_dict['subsample'] = False

            if 'codebook_path' in client_dict:
                _, codebook_rows = data_utils.read_csv(client_dict['codebook_path'],
                                                       has_header=True)
                # TODO: require specific codebook_header values? Or don't require a header,
                # and if the first value in the header is actually a data column name, assume
                # the first row is codebook data, not a header.

                # Create a dict indexed by column name
                codebook = dict()
                for codebook_row in codebook_rows:
                    codebook[codebook_row[0]] = dict(zip(['short_name', 'description', 'value_map'],
                                                     codebook_row[1:]))
                args_dict['codebook'] = codebook
            else:
                warning = dedent("""
                WARNING!

                You are creating a btable without a codebook, which will make interpretation
                of results more difficult. Codebooks should be in CSV format with each row
                corresponding to one column of the original data. The codebook should have four
                columns:

                1. actual column name
                2. short column description
                3. long column description
                4. value map (optional, only used for categorical columns - should be in JSON
                   format)
                """)
                print(warning)

            # Display warning messages and get confirmation if btable is too large.
            # Ask user if they want to turn on subsampling.
            max_columns = 200
            max_rows = 1000
            max_cells = 100000
            message = None
            if not yes:
                if len(rows[0]) > max_columns:
                    message = "The btable you are uploading has %d columns, but BayesDB is " \
                              "currently designed to support only %d columns. If you proceed, " \
                              "performance may suffer unless you set many columns' datatypes to " \
                              "'ignore'. Would you like to continue? Enter 'y' if yes." \
                              % (len(rows[0]), max_columns)
                if len(rows) > max_rows:
                    message = "The btable you are uploading has %d rows, but BayesDB is currently "\
                              "designed to support only %d rows. If you proceed, performance may "\
                              "suffer. Would you like to continue? Enter 'y' to continue without "\
                              "subsampling, 'n' to abort, 's' to continue by subsampling %d rows, "\
                              "or a positive integer to specify the number of rows to be "\
                              "subsampled." % (len(rows), max_rows, max_rows)
                if len(rows[0])*len(rows) > max_cells:
                    message = "The btable you are uploading has %d cells, but BayesDB is currently"\
                              " designed to support only %d cells. If you proceed, performance may"\
                              " suffer unless you enable subsampling. Enter 'y' to continue "\
                              " without subsampling, 'n' to abort, 's' to continue by subsampling "\
                              "%d rows, or a positive integer to specify the number of rows to be "\
                              "subsampled." % (len(rows)*len(rows[0]), max_cells, max_rows)
                if message is not None:
                    print(message)
                    user_confirmation = raw_input()
                    if 'y' == user_confirmation.strip():
                        pass
                    elif 'n' == user_confirmation.strip():
                        return dict(message="Operation canceled by user.")
                    elif 's' == user_confirmation.strip():
                        args_dict['subsample'] = min(max_rows, len(rows))
                    elif utils.is_int(user_confirmation.strip()):
                        args_dict['subsample'] = int(user_confirmation.strip())
                    else:
                        return dict(message="Operation canceled by user.")
        elif method_name in ['label_columns', 'update_metadata']:
            if client_dict['source'] == 'file':
                header, rows = data_utils.read_csv(client_dict['csv_path'])
                args_dict['mappings'] = {key: value for key, value in rows}

        # Call engine.
        result = self.call_bayesdb_engine(method_name, args_dict, debug)

        # If error occurred, exit now.
        if 'error' in result and result['error']:
            if pretty:
                print(result['message'])
                if force_output:
                    return result
                else:
                    return result['message']
            else:
                return result

        # Do stuff now that engine has given you output, but before printing the result.
        result = self.callback(method_name, args_dict, client_dict, result)

        if return_raw_result:
            raw_result = {
                'result': result,
                'method_name': method_name,
                'client_dict': client_dict}
            print("returning raw result for %s" % (method_name))
            return raw_result

        assert type(result) != int

        if timing:
            end_time = time.time()
            print('Elapsed time: %.2f seconds.' % (end_time - start_time))

        if plots is None:
            plots = 'DISPLAY' in os.environ.keys()

        if 'matrix' in result and (plots or client_dict['filename']):
            # Plot matrices
            plotting_utils.plot_matrix(result['matrix'], result['column_names'], result['title'],
                                       client_dict['filename'])
            if pretty:
                if 'column_lists' in result:
                    print(self.pretty_print(dict(column_lists=result['column_lists'])))

                if force_output:
                    return result
                else:
                    return self.pretty_print(result)
            else:
                return result
        if ('plot' in client_dict and client_dict['plot']):
            if (plots or client_dict['filename']):
                # Plot generalized histograms or scatterplots

                try:
                    plotting_M_c = result['metadata_full']['M_c_full']
                except KeyError:
                    plotting_M_c = result['M_c']

                plot_remove_key = method_name in ['select', 'infer']
                plotting_utils.plot_general_histogram(result['column_names'], result['data'],
                                                      plotting_M_c, result['schema_full'],
                                                      client_dict['filename'],
                                                      client_dict['scatter'],
                                                      remove_key=plot_remove_key)
                return self.pretty_print(result)
            else:
                if 'message' not in result:
                    result['message'] = ""
                result['message'] = "Your query indicates that you would like to make a plot, but "\
                                    "in order to do so, you must either enable plotting in a "\
                                    "window or specify a filename to save to by appending 'SAVE "\
                                    "TO <filename>' to this command.\n" + result['message']

        if pretty:
            pp = self.pretty_print(result)
            print(pp)

        # Print warnings last so they're readable without scrolling backwards.
        if 'warnings' in result:
            """ Pretty-print warnings. """
            for warning in result['warnings']:
                print('WARNING: %s' % warning)

        if pandas_output and 'data' in result and 'column_labels' in result:
            result_pandas_df = data_utils.construct_pandas_df(result)
            return result_pandas_df
        else:
            return result

    def callback(self, method_name, args_dict, client_dict, result):
        """
        This method is meant to be called after receiving the result of a
        call to the BayesDB engine, and modifies the output before it is displayed
        to the user.
        """
        if method_name == 'save_models':
            samples_dict = result
            # Here is where the models get saved.
            pkl_path = client_dict['pkl_path']
            if pkl_path[-7:] != '.pkl.gz':
                if pkl_path[-4:] == '.pkl':
                    pkl_path = pkl_path + ".gz"
                else:
                    pkl_path = pkl_path + ".pkl.gz"
            samples_file = gzip.GzipFile(pkl_path, 'wb')
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
        if 'data' in query_obj and 'column_labels' in query_obj:
            """ Pretty-print data table """
            pt = prettytable.PrettyTable()
            columns = query_obj['column_labels']
            pt.field_names = columns

            # Adjust value width - for now preserve 2 decimal places.
            for row_idx, row_values in enumerate(query_obj['data']):
                if type(row_values) == tuple:
                    row_values = list(row_values)
                for col_idx, col_value in enumerate(row_values):
                    if type(col_value) == float:
                        # Right-align numeric columns.
                        if row_idx == 0:
                            pt.align[columns[col_idx]] = 'r'
                        row_values[col_idx] = "% .2f" % col_value
                pt.add_row(row_values)
            result += str(pt)

        elif 'list' in query_obj:
            """ Pretty-print lists """
            result += str(query_obj['list'])
        elif 'column_names' in query_obj:
            """ Pretty-print cctypes """
            colnames = query_obj['column_names']
            zmatrix = query_obj['matrix']
            pt = prettytable.PrettyTable(hrules=prettytable.ALL, vrules=prettytable.ALL,
                                         header=False)
            pt.add_row([''] + list(colnames))
            for row, colname in zip(zmatrix, list(colnames)):
                pt.add_row([colname] + list(row))
            result += str(pt)
        elif 'column_labels' in query_obj:
            """ Pretty-print column list."""
            pt = prettytable.PrettyTable()
            pt.field_names = ['column']
            for column in query_obj['column_labels']:
                pt.add_row([column])
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
                print("%s:" % name)
                pt = prettytable.PrettyTable()
                pt.field_names = clist
                print(pt)
        elif 'models' in query_obj:
            """ Pretty-print model info. """
            pt = prettytable.PrettyTable()
            pt.field_names = ('model_id', 'iterations')
            for (id, iterations) in query_obj['models']:
                pt.add_row((id, iterations))
            result += str(pt)

        if len(result) >= 1 and result[-1] == '\n':
            result = result[:-1]
        return result

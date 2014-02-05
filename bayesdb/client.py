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

import crosscat.utils.api_utils as au

import utils
from parser import Parser
from engine import Engine

class Client(object):
    def __init__(self, hostname=None, port=8008, crosscat_engine_type='multiprocessing'):
        """
        Create a client object. The client creates a parser, that is uses to parse all commands,
        and an engine, which is uses to execute all commands. The engine can be remote or local.
        If local, the engine will be created.
        """
        self.parser = Parser()
        if hostname is None or hostname=='localhost':
            self.online = False
            self.engine = Engine(crosscat_engine_type)
        else:
            self.online = True
            self.hostname = hostname
            self.port = port
            self.URI = 'http://' + hostname + ':%d' % port

    def call_bayesdb_engine(self, method_name, args_dict):
        """
        Helper function used to call the BayesDB engine, whether it is remote or local.
        Accepts method name and arguments for that method as input.
        """
        if self.online:
            out, id = au.call(method_name, args_dict, self.URI)
        else:
            method = getattr(self.engine, method_name)
            argnames = inspect.getargspec(method)[0]
            args = [args_dict[argname] for argname in argnames if argname in args_dict]
            out = method(*args)
        return out

    def __call__(self, call_input, pretty=True, timing=False, wait=False, plots=None, yes=False):
        """Wrapper around execute."""
        return self.execute(call_input, pretty, timing, wait, plots, yes)

    def execute(self, call_input, pretty=True, timing=False, wait=False, plots=None, yes=False):
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

        if not pretty:
            return_list = []
            
        lines = self.parser.parse(bql_string)
        # Iterate through lines with while loop so we can append within loop.
        while len(lines) > 0:
            line = lines.pop(0)
            if type(call_input) == file:
                print '> %s' % line
            if wait:
                user_input = raw_input()
                if len(user_input) > 0 and (user_input[0] == 'q' or user_input[0] == 's'):
                    continue
            result = self.execute_statement(line, pretty=pretty, timing=timing, plots=plots, yes=yes)

            if type(result) == dict and result['message'] == 'execute_file':
                ## special case for one command: execute_file
                new_lines = self.parser.parse(result['bql_string'])
                lines += new_lines
            elif not pretty:
                return_list.append(result)
            if type(call_input) == file:
                print

        self.parser.reset_root_dir()
        
        if not pretty:
            return return_list

    def execute_statement(self, bql_statement_string, pretty=True, timing=False, plots=None, yes=False):
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

        out  = self.parser.parse_statement(bql_statement_string)
        if out is None:
            print "Could not parse command. Try typing 'help' for a list of all commands."
            return
        elif not out:
            return
            
        method_name, args_dict = out
        if method_name == 'execute_file':
            return dict(message='execute_file', bql_string=open(filename, 'r').read())
        elif method_name == 'drop_btable' and (not yes):
            ## If dropping something, ask for confirmation.
            print "Are you sure you want to permanently delete this btable? Enter 'y' if yes."
            user_confirmation = raw_input()
            if 'y' != user_confirmation.strip():
                return dict(message="Operation canceled by user.")
        result = self.call_bayesdb_engine(method_name, args_dict)
        result = self.callback(method_name, args_dict, result)
        assert type(result) != int
        
        if timing:
            end_time = time.time()
            print 'Elapsed time: %.2f seconds.' % (end_time - start_time)

        if plots is None:
            # TODO: should this be commented or not?
            #plots = 'DISPLAY' in os.environ.keys()
            plots = False

        if 'matrix' in result:
            ## Special logic to display matrices.
            if plots:
                plotting_utils.plot_matrix(result['matrix'], result['column_names'], title=result['title'], filename=None)                            
            else:
                pp = self.pretty_print(result)
                print pp
                return pp
        elif pretty:
            if type(result) == dict and 'message' in result.keys():
                print result['message']
            pp = self.pretty_print(result)
            print pp
            return pp
        else:
            if type(result) == dict and 'message' in result.keys():
                print result['message']
            return result

    def callback(self, method_name, args_dict, result):
        """
        This method is meant to be called after receiving the result of a
        call to the BayesDB engine, and modifies the output before it is displayed
        to the user.
        """
        if method_name == 'save_models':
            samples_dict = result
            ## Here is where the models get saved.
            samples_file = gzip.GzipFile(args_dict['pkl_path'], 'w')
            pickle.dump(samples_dict, samples_file)
            return dict(message="Successfully saved the samples to %s" % args_dict['pkl_path'])
        else:
            return result
        
    def pretty_print(self, query_obj):
        """
        Return a pretty string representing the output object.
        """
        result = ""
        if type(query_obj) == dict and 'data' in query_obj and 'columns' in query_obj:
            """ Pretty-print data table """
            pt = prettytable.PrettyTable()
            pt.field_names = query_obj['columns']
            for row in query_obj['data']:
                pt.add_row(row)
            result = pt
        elif type(query_obj) == list and len(query_obj) > 0 and type(query_obj[0]) == tuple:
            pt = prettytable.PrettyTable()
            ## TODO
            return "TODO"
        elif type(query_obj) == list:
            """ Pretty-print lists """
            result = str(query_obj)
        elif type(query_obj) == dict and 'column_names' in query_obj:
            """ Pretty-print cctypes """
            colnames = query_obj['column_names']
            zmatrix = query_obj['matrix']
            pt = prettytable.PrettyTable(hrules=prettytable.ALL, vrules=prettytable.ALL, header=False)
            pt.add_row([''] + list(colnames))
            for row, colname in zip(zmatrix, list(colnames)):
                pt.add_row([colname] + list(row))
            result = pt
        elif type(query_obj) == dict and 'columns' in query_obj:
            """ Pretty-print column list."""
            pt = prettytable.PrettyTable()
            pt.field_names = query_obj['columns']
            result = pt
        elif type(query_obj) == dict and 'models' in query_obj:
            """ Prety-print model info. """
            m = query_obj['models']
            output_list = ['Model %d: %d iterations' % (id, iterations) for id,iterations in m]
            result = ', '.join(output_list)
        return result




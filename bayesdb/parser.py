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
import bql_grammar as bql
import pyparsing as pp

class Parser(object):
    def __init__(self):
        self.reset_root_dir()

    def pyparse_input(self, input_string):
        """Uses the grammar defined in bql_grammar to create a pyparsing object out of an input string"""
        try:
            bql_blob_ast = bql.bql_input.parseString(input_string)
        except pp.ParseException as x:
            raise utils.BayesDBParseError("Invalid query: Could not parse '%s'" %input_string) #TODO get character number
        return bql_blob_ast
        
    def split_statements(self,bql_blob_ast):
        pass

    def parse_single_statement(self,bql_statement_ast):
        ## TODO Check for nest
        parse_method = getattr(self,'parse_' + bql_statement_ast.statement_id)
        return parse_method(bql_statement_ast)

#####################################################################################
## -------------------------- Individual Parse Methods --------------------------- ##
#####################################################################################

    def parse_list_btables(self,bql_statement_ast):
        if bql_statement_ast.statement_id == "list_btables":
            return 'list_btables', dict(), None
        else:
            raise utils.BayesDBParseError("Parsing statement as LIST BTABLES failed")

    def parse_execute_file(self,bql_statement_ast):
        print "execute_file"

    def parse_show_schema(self,bql_statement_ast):
        print "show_schema"

    def parse_show_models(self,bql_statement_ast):
        print "show_models"

    def parse_show_diagnostics(self,bql_statement_ast):
        print "show_diagnostics"

    def parse_drop_models(self,bql_statement_ast):
        print "drop_models"

    def parse_initialize_models(self,bql_statement_ast):
        print "initialize_models"

    def parse_create_btable(self,bql_statement_ast)
        print "create_btable"

    def parse_update_schema(self,bql_statement_ast):
        print "update_schema"

    def parse_drop_btable(self,bql_statement_ast):
        print "drop_btable"

    def parse_analyze(self,bql_statement_ast):
        print "parse_analyze"

    def parse_show_row_lists(self,bql_statement_ast):
        print "show_row_lists"

    def parse_show_column_lists(self,bql_statement_ast):
        print "show_column_lists"

    def parse_show_columns(self,bql_statement_ast):
        print "show_columns"

    def parse_save_models(self,bql_statement_ast):
        print "save_models"

    def parse_load_models(self,bql_statement_ast):
        print "load_models"


    def parse_infer(self,bql_statement_ast):
        print "infer"

    def parse_select(self,bql_statement_ast):
        print "select"

    def parse_simulate(self,bql_statement_ast):
        print "simulate"

    def parse_estimate_columns(self,bql_statement_ast):
        print "estimate_columns"

    def parse_estimate_pairwise_row(self,bql_statement_ast):
        print "estimate_pairwise_row"

    def parse_estimate_pairwise(self,bql_statement_ast):
        print "estimate_pairwise"


#####################################################################################
## --------------------------- Other Helper functions ---------------------------- ##
#####################################################################################


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
    
    

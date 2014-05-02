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
import ast
import functions

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
        """
        returns a list of bql statements, not necessarily useful. 
        """
        return [bql_statement_ast for bql_statement_ast in bql_blob_ast]

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
        return 'execute_file', dict(filename=self.get_absolute_path(bql_statement_ast.filename)), None

    def parse_show_schema(self,bql_statement_ast):
        return 'show_schema', dict(tablename=bql_statement_ast.btable), None

    def parse_show_models(self,bql_statement_ast):
        return 'show_models', dict(tablename=bql_statement_ast.btable), None

    def parse_show_diagnostics(self,bql_statement_ast):
        return 'show_diagnostics', dict(tablename=bql_statement_ast.btable), None

    def parse_drop_models(self,bql_statement_ast):
        model_indices = None
        if bql_statement_ast.index_clause != '':
            model_indices = bql_statement_ast.index_clause.asList()
        return 'drop_models', dict(tablename=bql_statement_ast.btable, model_indices=model_indices), None

    def parse_initialize_models(self,bql_statement_ast):
        n_models = int(bql_statement_ast.num_models)
        tablename = bql_statement_ast.btable
        arguments_dict = dict(tablename=tablename, n_models=n_models, model_config=None)
        if bql_statement_ast.config != '':
            arguments_dict['model_config'] = bql_statement_ast.config
        return 'initialize_models', arguments_dict, None

    def parse_create_btable(self,bql_statement_ast):
        tablename = bql_statement_ast.btable
        filename = self.get_absolute_path(bql_statement_ast.filename)
        return 'create_btable', dict(tablename=tablename, cctypes_full=None), dict(csv_path=filename)
        #TODO types?

    def parse_update_schema(self,bql_statement_ast):
        tablename = bql_statement_ast.btable
        mappings = dict()
        type_clause = bql_statement_ast.type_clause
        for update in type_clause:
            mappings[update[0]]=update[1]
        return 'update_schema', dict(tablename=tablename, mappings=mappings), None

    def parse_drop_btable(self,bql_statement_ast):
        return 'drop_btable', dict(tablename=bql_statement_ast.btable), None

    def parse_analyze(self,bql_statement_ast):
        model_indices = None
        iterations = None
        seconds = None
        kernel = 0
        tablename = bql_statement_ast.btable
        if bql_statement_ast.index_clause != '':
            model_indices = bql_statement_ast.index_clause.asList()
        if bql_statement_ast.num_seconds !='':
            seconds = int(bql_statement_ast.num_seconds)
        if bql_statement_ast.num_iterations !='':
            iterations = int(bql_statement_ast.num_iterations)
        if bql_statement_ast.with_kernel_clause != '':
            kernel = bql_statement_ast.with_kernel_clause.kernel_id
            if kernel == 'mh': ## TODO should return None or something for invalid kernels
                kernel=1
        return 'analyze', dict(tablename=tablename, model_indices=model_indices,
                                   iterations=iterations, seconds=seconds, ct_kernel=kernel), None
        
    def parse_show_row_lists(self,bql_statement_ast):
        return 'show_row_lists', dict(tablename=bql_statement_ast.btable), None

    def parse_show_column_lists(self,bql_statement_ast):
        return 'show_column_lists', dict(tablename=bql_statement_ast.btable), None

    def parse_show_columns(self,bql_statement_ast):
        return 'show_columns', dict(tablename=bql_statement_ast.btable), None

    def parse_save_models(self,bql_statement_ast):
        return 'save_models', dict(tablename=bql_statement_ast.btable), dict(pkl_path=bql_statement_ast.filename)

    def parse_load_models(self,bql_statement_ast):
        return 'load_models', dict(tablename=bql_statement_ast.btable), dict(pkl_path=bql_statement_ast.filename)

    def parse_infer(self,bql_statement_ast):
        print "infer"

    def parse_select(self,bql_statement_ast):
        ## TODO assert for extra pieces
        tablename = bql_statement_ast.btable
        functions = bql_statement_ast.functions
        summarize = (bql_statement_ast.summarize == 'summarize') #TODO should be mutually exclusive?
        plot = (bql_statement_ast.plot == 'plot')
        scatter = (bql_statement_ast.scatter == 'scatter') ##TODO add to grammar
        pairwise = (bql_statement_ast.pairwise == 'pairwise')
        whereclause = None
        if bql_statement_ast.where_conditions != '':
            whereclause = bql_statement_ast.where_conditions
        limit = float('inf')
        if bql_statement_ast.limit != '':
            limit = int(bql_statement_ast.limit)
        filename = None
        if bql_statement_ast.filename != '':
            filename = bql_statement_ast.filename
        order_by = False ##TODO maybe change to None
        if bql_statement_ast.order_by != '':
            order_by = bql_statement_ast.order_by.order_by_set.asList()
        modelids = None
        if bql_statement_ast.using_models_index_clause != '':
            modelids = bql_statement_ast.using_models_index_clause.asList()
        #TODO deprecate columnstring
        return 'select', dict(tablename=tablename, whereclause=whereclause, 
                              functions=functions, limit=limit, order_by=order_by, plot=plot, 
                              modelids=modelids, summarize=summarize), \
            dict(pairwise=pairwise, scatter=scatter, filename=filename, plot=plot)

    def parse_simulate(self,bql_statement_ast):
        print "simulate"

    def parse_estimate_columns(self,bql_statement_ast):
        print "estimate_columns"

    def parse_estimate_pairwise_row(self,bql_statement_ast):
        print "estimate_pairwise_row"

    def parse_estimate_pairwise(self,bql_statement_ast):
        print "estimate_pairwise"

#####################################################################################
## ------------------------------ Function parsing ------------------------------- ##
#####################################################################################
    def get_args_pred_prob(self, function_group, M_c):
        """
        returns the column index from a predictive probability function
        raises exceptions for unfound columns
        """
        if function_group.column != '' and function_group.column in M_c['name_to_idx']:
            column = function_group.column
            c_idx = M_c['name_to_idx'][column]
            return c_idx
        elif function_group.column != '':
            raise utils.BayesDBParseError("Invalid query: could not parse '%s'" % function_group.column)
        else:
            raise utils.BayesDBParseError("Invalid query: missing column argument")

    def get_args_prob(self,function_group, M_c):
        """
        Returns column_index, value from a probability function
        raises exception for unfound columns
        """
        if function_group.column != '' and function_group.column in M_c['name_to_idx']:
            column = function_group.column
            c_idx = M_c['name_to_idx'][column]
        elif function_group.column != '':
            raise utils.BayesDBParseError("Invalid query: could not parse '%s'" % function_group.column)
        else:
            raise utils.BayesDBParseError("Invalid query: missing column argument")
        value = utils.string_to_column_type(function_group.value, column, M_c)
        return c_idx, value
    
    def get_args_similarity(self,function_group, M_c, T, column_lists):
        """
        returns the target_row_id and a list of with_respect_to columns based on 
        similarity function
        Raises exception for unfound columns
        """
        ##TODO some cleaining with row_clause
        target_row_id = None
        target_columns = None
        if function_group != '':
            ## Case for given row_id
            if function_group.row_id != '':
                target_row_id = int(function_group.row_id)
            ## Case for format column = value
            elif function_group.column != '':
                assert T is not None
                target_col_name = function_group.column
                target_col_value = function_group.column_value
                target_row_id = utils.row_id_from_col_value(target_col_value, target_col_name, M_c, T)
        ## With respect to clause
        with_respect_to_clause = function_group.with_respect_to
        if with_respect_to_clause !='':

            column_set = with_respect_to_clause.column_list
            target_column_names = []
            for column_name in column_set:
                if column_name == '*':
                    target_columns = None
                    break
                elif column_lists is not None and column_name in column_lists.keys():
                    target_column_names.append(column_lists[column_name])
                elif column_name in M_c['name_to_idx']:
                    target_column_names.append(column_name)
                else:
                    raise utils.BayesDBParseError("Invalid query: column '%s' not found" % column_name)
            target_columns = [M_c['name_to_idx'][column_name] for column_name in target_column_names]
        return target_row_id, target_columns

    def get_args_typicality(self,function_group, M_c):
        """
        returns column_index if present, if not, returns None. 
        if invalid column, raises exception
        """
        if function_group.column == '':
            return None
        else:
            return utils.get_index_from_colname(M_c, function_group.column)

    def get_args_of_with(self,function_group, M_c):
        """
        designed to handle dependence probability, mutual information, and correlation function_groups
        all have an optional of clause
        returns of_column_index, with_column_index
        invalid column raises exception
        """
        with_column = function_group.with_column
        with_column_index = utils.get_index_from_colname(M_c, with_column)
        of_column_index = None
        if function_group.of_column != '':
            of_column_index = utils.get_index_from_colname(M_c, function_group.of_column)
        return of_column_index, with_column_index 

#####################################################################################
## ----------------------------- Sub query parsing  ------------------------------ ##
#####################################################################################

    def parse_where_clause(self, where_clause_ast, M_c, T, column_lists): ##Deprecate select_utils.get_conditions_from_whereclause
        """
        Creates conditions: the list of conditions in the whereclause
        List of (c_idx, op, val)
        """
        conditions = []
        operator_map = {'<=': operator.le, '<': operator.lt, '=': operator.eq,
                        '>': operator.gt, '>=': operator.ge, 'in': operator.contains}
        for single_condition in where_clause_ast.where_conditions:
            ## TODO implement confidence in whereclause
            pass
            
        
        

        return conditions
#        print "where_clause"

    def parse_order_by_clause(self, order_by_clause_ast):
        print "order_by"

    def parse_functions(self, function_groups, M_c=None, T=None, column_lists=None):
        '''
        Generates two lists of functions, arguments, aggregate tuples. 
        Returns queries, query_colnames
        
        queries is a list of (query_function, query_args, aggregate) tuples,
        where query_function is: row_id, column, probability, similarity.
    
        For row_id: query_args is ignored (so it is None).
        For column: query_args is a c_idx.
        For probability: query_args is a (c_idx, value) tuple.
        For similarity: query_args is a (target_row_id, target_column) tuple.
        '''
        ## Always return row_id as the first column.
        query_colnames = ['row_id']
        queries = [(functions._row_id, None, False)]

        for function_group in function_groups: ##TODO throw exception, make safe
            if function_group.function_id == 'predictive probability':
                queries.append((functions._predictive_probability, 
                                self.get_args_pred_prob(function_group, M_c), 
                                False))
            elif function_group.function_id == 'typicality':
                if function_group.column != '':
                    queries.append((functions._col_typicality, 
                                    self.get_args_typicality(function_group, M_c), 
                                    True))
                else:
                    queries.append((functions._row_typicality,
                                    self.get_args_typicality(function_group, M_c), 
                                    False))
            elif function_group.function_id == 'probability':
                queries.append((functions._probability, 
                                self.get_args_prob(function_group, M_c), 
                                True))
            elif function_group.function_id == 'similarity to':
                assert M_c is not None
                queries.append((functions._similarity, 
                                self.get_args_similarity(function_group, M_c, T, column_lists), 
                                False))
            elif function_group.function_id == 'dependence probability':
                queries.append((functions._dependence_probability, 
                                self.get_args_of_with(function_group, M_c), 
                                True))
            elif function_group.function_id == 'mutual information':
                queries.append((functions._mutual_information, 
                                self.get_args_of_with(function_group, M_c), 
                                True))
            elif function_group.function_id == 'correlation':
                queries.append((functions._correlation, 
                                self.get_args_of_with(function_group, M_c), 
                                True))
            ## single column, column_list, or *
            ## TODO maybe split to function
            ## TODO handle nesting
            elif function_group.column_id != '':
                column_name = function_group.column_id
                if column_name == '*':
                    assert M_c is not None
                    all_columns = utils.get_all_column_names_in_original_order(M_c)
                    index_list = [M_c['name_to_idx'][column_name] for column_name in all_columns]
                elif (column_lists is not None) and (column_name in column_lists.keys()):
                    index_list = column_lists[column_name]
                elif column_name in M_c['name_to_idx']:
                    index_list = [M_c['name_to_idx'][column_name]]
                else:
                    raise utils.BayesDBParseError("Invalid query: could not parse '%s'" % column_name)
                queries += [(functions._column, column_index , False) for column_index in index_list]

        return queries, query_colnames

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

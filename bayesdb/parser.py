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

import utils
import os
import bql_grammar as bql
import pyparsing as pp
#import ast
import functions
import operator

class Parser(object):
    def __init__(self):
        self.reset_root_dir()

    def pyparse_input(self, input_string):
        """Uses the grammar defined in bql_grammar to create a pyparsing object out of an input string"""
        try:
            bql_blob_ast = bql.bql_input.parseString(input_string, parseAll=True)
        except pp.ParseException as x:
            raise utils.BayesDBParseError("Invalid query. Could not parse (Line {e.lineno}, column {e.col}):\n\t'{e.line}'".format(e=x))
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

    def parse_label_columns(self, bql_statement_ast): ##TODO only smoke test right now
        tablename = bql_statement_ast.btable
        source = None
        mappings = None
        if bql_statement_ast.label_clause != '':
            source = 'inline'
            mappings = {}
            for label_set in bql_statement_ast.label_clause:
                mappings[label_set[0]] = label_set[1]
        csv_path = None
        if bql_statement_ast.filename != '':
            csv_path = bql_statement_ast.filename
            source = 'file'
        return 'label_columns', \
            dict(tablename=tablename, mappings=mappings), \
            dict(source=source, csv_path=csv_path)

    def parse_show_metadata(self, bql_statement_ast):
        tablename = None
        if bql_statement_ast.btable != '':
            tablename = bql_statement_ast.btable
        keyset = None
        if bql_statement_ast.keyset != '':
            keyset = bql_statement_ast.keyset
        return 'show_metadata', dict(tablename=tablename, keyset=keyset), None

    def parse_show_label(self, bql_statement_ast):
        tablename = None
        if bql_statement_ast.btable != '':
            tablename = bql_statement_ast.btable
        columnset = None
        if bql_statement_ast.columnset != '':
            columnset = bql_statement_ast.columnset
        return 'show_labels', dict(tablename=tablename, columnset=columnset), None

    def parse_update_metadata(self, bql_statement_ast):
        tablename = bql_statement_ast.btable
        source = None
        mappings = None
        if bql_statement_ast.label_clause != '':
            source = 'inline'
            mappings = {}
            for label_set in bql_statement_ast.label_clause:
                mappings[label_set[0]] = label_set[1]
        csv_path = None
        if bql_statement_ast.filename != '':
            csv_path = bql_statement_ast.filename
            source = 'file'
        return 'update_metadata', \
            dict(tablename=tablename, mappings=mappings), \
            dict(source=source, csv_path=csv_path)
    
    def parse_query(self, bql_statement_ast):
        '''
        master parser for queries (select, infer, simulate, estimate pairwise, etc)
        returns a general args dict which the specific versions of those functions 
        will then trim and check for illegal aruguments through assertions. 
        '''
        statement_id = bql_statement_ast.statement_id 
        
        confidence = 0
        if bql_statement_ast.confidence != '':
            confidence = float(bql_statement_ast.confidence)
            if confidence > 1: 
                raise utils.BayesDBParseError("Confidence cannot be greater than 0.")
        filename = None
        if bql_statement_ast.filename != '':
            filename = bql_statement_ast.filename
        functions = bql_statement_ast.functions
        givens = None
        if bql_statement_ast.given_clause != '':
            givens = bql_statement_ast.given_clause
        limit = float('inf')
        if bql_statement_ast.limit != '':
            limit = int(bql_statement_ast.limit)
        modelids = None
        if bql_statement_ast.using_models_index_clause != '':
            modelids = bql_statement_ast.using_models_index_clause.asList()
        name = None
        if bql_statement_ast.as_column_list != '':
            ## TODO name is a bad name
            name = bql_statement_ast.as_column_list
        newtablename=None ##TODO implement into
        numpredictions = None
        if bql_statement_ast.times != '':
            numpredictions = int(bql_statement_ast.times)
        numsamples = None
        if bql_statement_ast.samples != '':
            numsamples = int(bql_statement_ast.samples)
        order_by = False
        if bql_statement_ast.order_by != '':
            order_by = bql_statement_ast.order_by
        plot=(bql_statement_ast.plot == 'plot')
        pairwise = (bql_statement_ast.pairwise == 'pairwise')
        column_list = None
        if bql_statement_ast.columns != '':
            column_list = bql_statement_ast.columns[0] ##TODO implement allowing comma separated columns here
            assert len(bql_statement_ast.columns) < 2
        row_list = None
        if bql_statement_ast.rows != '':
            row_list = bql_statement_ast.rows ##TODO parse to list of rows
        scatter = (bql_statement_ast.scatter == 'scatter') ##TODO add to grammar
        summarize=(bql_statement_ast.summarize == 'summarize')
        hist = (bql_statement_ast.hist == 'hist')
        tablename = bql_statement_ast.btable
        components_name = None
        threshold = None
        if bql_statement_ast.connected_components_clause != '':
            components_name = bql_statement_ast.connected_components_clause.as_label
            threshold = float(bql_statement_ast.connected_components_clause.threshold)
        whereclause = None
        if bql_statement_ast.where_conditions != '':
            whereclause = bql_statement_ast.where_conditions

        return statement_id, \
            dict(components_name=components_name,
                 confidence = confidence,
                 functions=functions,
                 givens=givens,
                 limit=limit,
                 modelids=modelids,
                 name=name,
                 newtablename=newtablename,
                 numpredictions=numpredictions,
                 numsamples=numsamples,
                 order_by=order_by,
                 plot=plot,
                 column_list=column_list,
                 row_list=row_list,
                 summarize=summarize,
                 hist=hist,
                 tablename=tablename,
                 threshold=threshold,
                 whereclause=whereclause), \
            dict(plot=plot, 
                 scatter=scatter, 
                 pairwise=pairwise, 
                 filename=filename)

    def parse_infer(self,bql_statement_ast):
        method_name, args_dict, client_dict = self.parse_query(bql_statement_ast)
        tablename = args_dict['tablename']
        functions = args_dict['functions']
        summarize = args_dict['summarize']
        hist = args_dict['hist']
        plot = args_dict['plot']
        whereclause = args_dict['whereclause']
        limit = args_dict['limit']
        order_by = args_dict['order_by']
        modelids = args_dict['modelids']
        newtablename = args_dict['newtablename']
        confidence = args_dict['confidence']
        numsamples = args_dict['numsamples']

        pairwise = client_dict['pairwise']
        filename = client_dict['filename']
        scatter = client_dict['scatter']

        assert args_dict['components_name'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS clause not allowed in INFER"
        assert args_dict['threshold'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS clause not allowed in INFER"
        assert args_dict['givens'] == None, "BayesDBParsingError: GIVENS clause not allowed in INFER"
        assert args_dict['name'] == None, "BayesDBParsingError: SAVE AS <column_list> clause not allowed in INFER"
        assert args_dict['numpredictions'] == None, "BayesDBParsingError: TIMES clause not allowed in INFER"
        assert args_dict['column_list'] == None, "BayesDBParsingError: FOR <columns> clause not allowed in INFER"
        assert args_dict['row_list'] == None, "BayesDBParsingError: FOR <rows> not allowed in INFER"
        for function in functions:
            assert function.function_id == '', "BayesDBParsingError: %s not valid in INFER" % function.function_id
                
        
        return 'infer', \
            dict(tablename=tablename, functions=functions, 
                 newtablename=newtablename, confidence=confidence, 
                 whereclause=whereclause, limit=limit,
                 numsamples=numsamples, order_by=order_by, 
                 plot=plot, modelids=modelids, summarize=summarize, hist=hist), \
            dict(plot=plot, scatter=scatter, pairwise=pairwise, filename=filename)

    def parse_select(self,bql_statement_ast):
        method_name, args_dict, client_dict = self.parse_query(bql_statement_ast)
        tablename = args_dict['tablename']
        functions = args_dict['functions']
        summarize = args_dict['summarize']
        hist = args_dict['hist']
        plot = args_dict['plot']
        whereclause = args_dict['whereclause']
        limit = args_dict['limit']
        order_by = args_dict['order_by']
        modelids = args_dict['modelids']

        pairwise = client_dict['pairwise']
        filename = client_dict['filename']
        scatter = client_dict['scatter']

        assert args_dict['components_name'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS clause not allowed in SELECT"
        assert args_dict['threshold'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS clause not allowed in SELECT"
        assert args_dict['givens'] == None, "BayesDBParsingError: GIVENS clause not allowed in SELECT"
        assert args_dict['name'] == None, "BayesDBParsingError: SAVE AS <column_list> clause not allowed in SELECT"
        assert args_dict['numpredictions'] == None, "BayesDBParsingError: TIMES clause not allowed in SELECT"
        assert args_dict['column_list'] == None, "BayesDBParsingError: FOR <columns> clause not allowed in SELECT"
        assert args_dict['row_list'] == None, "BayesDBParsingError: FOR <rows> not allowed in SELECT"
        assert args_dict['confidence'] == 0, "BayesDBParsingError: CONFIDENCE not allowed in SELECT"
        assert args_dict['numsamples'] == None, "BayesDBParsingError: WITH SAMPLES not allowed in SELECT"

        return 'select', \
            dict(tablename=tablename, whereclause=whereclause, 
                 functions=functions, limit=limit, order_by=order_by, plot=plot, 
                 modelids=modelids, summarize=summarize, hist=hist), \
            dict(pairwise=pairwise, scatter=scatter, filename=filename, plot=plot)

    def parse_simulate(self,bql_statement_ast):
        method_name, args_dict, client_dict = self.parse_query(bql_statement_ast)
        tablename = args_dict['tablename']
        functions = args_dict['functions']
        summarize = args_dict['summarize']
        hist = args_dict['hist']
        plot = args_dict['plot'] 
        order_by = args_dict['order_by']
        modelids = args_dict['modelids']
        newtablename = args_dict['newtablename']
        givens = args_dict['givens']
        numpredictions = args_dict['numpredictions']
       
        pairwise = client_dict['pairwise']
        filename = client_dict['filename']
        scatter = client_dict['scatter']

        assert args_dict['components_name'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS clause not allowed in SIMULATE."
        assert args_dict['threshold'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS clause not allowed in SIMULATE."
        assert args_dict['name'] == None, "BayesDBParsingError: SAVE AS <column_list> clause not allowed in SIMULATE."
        assert args_dict['column_list'] == None, "BayesDBParsingError: FOR <columns> clause not allowed in SIMULATE."
        assert args_dict['row_list'] == None, "BayesDBParsingError: FOR <rows> not allowed in SIMULATE."
        assert args_dict['confidence'] == 0, "BayesDBParsingError: CONFIDENCE not allowed in SIMULATE."
        assert args_dict['numsamples'] == None, "BayesDBParsingError: WITH SAMPLES not allowed in SIMULATE."
        assert args_dict['whereclause'] == None, "BayesDBParsingError: whereclause not allowed in SIMULATE. Use GIVEN instead."
        for function in functions:
            assert function.function_id == '', "BayesDBParsingError: %s not valid in SIMULATE" % function.function_id

        return 'simulate', \
            dict(tablename=tablename, functions=functions, 
                 newtablename=newtablename, givens=givens, 
                 numpredictions=numpredictions, order_by=order_by, 
                 plot=plot, modelids=modelids, summarize=summarize, hist=hist), \
            dict(filename=filename, plot=plot, scatter=scatter, pairwise=pairwise)

    def parse_estimate(self,bql_statement_ast):
        method_name, args_dict, client_dict = self.parse_query(bql_statement_ast)
        assert args_dict['functions'][0] == 'column', "BayesDBParseError: must be ESTIMATE COLUMNS."
        functions = args_dict['functions']
        tablename = args_dict['tablename']
        whereclause = args_dict['whereclause']
        limit = args_dict['limit']
        order_by = args_dict['order_by']
        modelids = args_dict['modelids']
        name = args_dict['name']

        assert args_dict['components_name'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS not allowed in estimate columns."
        assert args_dict['confidence'] == 0, "BayesDBParsingError: WITH CONFIDENCE not allowed in estimate columns."
        assert args_dict['givens'] == None, "BayesDBParsingError: GIVENS not allowed in estimate columns."
        assert args_dict['newtablename'] == None, "BayesDBParsingError: INTO TABLE not allowed in estimate columns."
        assert args_dict['numpredictions'] == None, "BayesDBParsingError: TIMES not allowed in estimate columns."
        assert args_dict['numsamples'] == None, "BayesDBParsingError: WITH SAMPLES not allowed in estimate columns."
        assert args_dict['column_list'] == None, "BayesDBParsingError: FOR COLUMNS not allowed in estimate columns."
        assert args_dict['row_list'] == None, "BayesDBParsingError: FOR ROWS not allowed in estimate columns."
        assert args_dict['summarize'] == False, "BayesDBParsingError: SUMMARIZE not allowed in estimate columns."
        assert args_dict['hist'] == False, "BayesDBParsingError: HIST not allowed in estimated columns."
        assert args_dict['threshold'] == None, "BayesDBParsingError: SAVE CONNECTED COMPONENTS not allowed in estimate columns."
        assert args_dict['plot'] == False, "BayesDBParsingError: PLOT not allowed in estimate columns."

        assert client_dict['plot'] == False, "BayesDBParsingError: PLOT not allowed in estimate columns."
        assert client_dict['scatter'] == False, "BayesDBParsingError: SCATTER not allowed in estimate columns."
        assert client_dict['pairwise'] == False, "BayesDBParsingError: PAIRWISE not allowed in estimate columns."
        assert client_dict['filename'] == None, "BayesDBParsingError: AS FILE not allowed in estimate columns."

        return 'estimate_columns', \
            dict(tablename=tablename, functions=functions, 
                 whereclause=whereclause, limit=limit, 
                 order_by=order_by, name=name, modelids=modelids), \
            None

    def parse_estimate_pairwise_row(self,bql_statement_ast):
        method_name, args_dict, client_dict = self.parse_query(bql_statement_ast)
        functions = args_dict['functions'][0]
        assert len(args_dict['functions']) == 1, "BayesDBParsingError: Only one function allowed in estimate pairwise."
        tablename = args_dict['tablename']
        row_list = args_dict['row_list']
        components_name = args_dict['components_name']
        threshold = args_dict['threshold']
        modelids = args_dict['modelids']
        filename = client_dict['filename']

        assert args_dict['confidence'] == 0, "BayesDBParsingError: WITH CONFIDENCE not allowed in ESTIMATE PAIRWISE."
        assert args_dict['givens'] == None, "BayesDBParsingError: GIVENS not allowed in ESTIMATE PAIRWISE."
        assert args_dict['newtablename'] == None, "BayesDBParsingError: INTO TABLE not allowed in ESTIMATE PAIRWISE."
        assert args_dict['numpredictions'] == None, "BayesDBParsingError: TIMES not allowed in ESTIMATE PAIRWISE."
        assert args_dict['numsamples'] == None, "BayesDBParsingError: WITH SAMPLES not allowed in ESTIMATE PAIRWISE."
        assert args_dict['column_list'] == None, "BayesDBParsingError: FOR COLUMNS not allowed in ESTIMATE PAIRWISE."
        assert args_dict['summarize'] == False, "BayesDBParsingError: SUMMARIZE not allowed in ESTIMATE PAIRWISE."
        assert args_dict['hist'] == False, "BayesDBParsingError: HIST not allowed in ESTIMATE PAIRWISE."
        assert args_dict['plot'] == False, "BayesDBParsingError: PLOT not allowed in ESTIMATE PAIRWISE."
        assert args_dict['whereclause'] == None, "BayesDBParsingError: WHERE not allowed in ESTIMATE PAIRWISE."

        assert client_dict['plot'] == False, "BayesDBParsingError: PLOT not allowed in ESTIMATE PAIRWISE."
        assert client_dict['scatter'] == False, "BayesDBParsingError: SCATTER not allowed in ESTIMATE PAIRWISE."
        assert client_dict['pairwise'] == False, "BayesDBParsingError: PAIRWISE not allowed in ESTIMATE PAIRWISE."

        return 'estimate_pairwise_row', \
            dict(tablename=tablename, function=functions,
                 row_list=row_list, components_name=components_name, 
                 threshold=threshold, modelids=modelids), \
            dict(filename=filename)

    def parse_estimate_pairwise(self,bql_statement_ast):
        method_name, args_dict, client_dict = self.parse_query(bql_statement_ast)
        functions = args_dict['functions']
        assert len(args_dict['functions']) == 1, "BayesDBParsingError: Only one function allowed in estimate pairwise."
        assert functions[0].function_id in ['correlation', 'mutual information', 'dependence probability']
        function_name = functions[0].function_id

        tablename = args_dict['tablename']
        column_list = args_dict['column_list']
        components_name = args_dict['components_name']
        threshold = args_dict['threshold']
        modelids = args_dict['modelids']
        filename = client_dict['filename']

        assert args_dict['confidence'] == 0, "BayesDBParsingError: WITH CONFIDENCE not allowed in ESTIMATE PAIRWISE."
        assert args_dict['givens'] == None, "BayesDBParsingError: GIVENS not allowed in ESTIMATE PAIRWISE."
        assert args_dict['newtablename'] == None, "BayesDBParsingError: INTO TABLE not allowed in ESTIMATE PAIRWISE."
        assert args_dict['numpredictions'] == None, "BayesDBParsingError: TIMES not allowed in ESTIMATE PAIRWISE."
        assert args_dict['numsamples'] == None, "BayesDBParsingError: WITH SAMPLES not allowed in ESTIMATE PAIRWISE."
        assert args_dict['row_list'] == None, "BayesDBParsingError: FOR ROWS not allowed in ESTIMATE PAIRWISE."
        assert args_dict['summarize'] == False, "BayesDBParsingError: SUMMARIZE not allowed in ESTIMATE PAIRWISE."
        assert args_dict['hist'] == False, "BayesDBParsingError: HIST not allowed in ESTIMATE PAIRWISE."
        assert args_dict['plot'] == False, "BayesDBParsingError: PLOT not allowed in ESTIMATE PAIRWISE."
        assert args_dict['whereclause'] == None, "BayesDBParsingError: whereclause not allowed in ESTIMATE PAIRWISE"

        assert client_dict['plot'] == False, "BayesDBParsingError: PLOT not allowed in ESTIMATE PAIRWISE."
        assert client_dict['scatter'] == False, "BayesDBParsingError: SCATTER not allowed in ESTIMATE PAIRWISE."
        assert client_dict['pairwise'] == False, "BayesDBParsingError: PAIRWISE not allowed in ESTIMATE PAIRWISE."

        return 'estimate_pairwise', \
            dict(tablename=tablename, function_name=function_name,
                 column_list=column_list, components_name=components_name, 
                 threshold=threshold, modelids=modelids), \
            dict(filename=filename)

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
                    target_column_names += column_lists[column_name]
                elif column_name in M_c['name_to_idx']:
                    target_column_names.append(column_name)
                else:
                    raise utils.BayesDBParseError("Invalid query: column '%s' not found" % column_name)
            target_columns = [M_c['name_to_idx'][column_name] for column_name in target_column_names]
        return target_row_id, target_columns

    def get_args_typicality(self,function_group, M_c):
        """
        returns column_index if present, if not, returns True. ##TODO this needs a ton of testing
        if invalid column, raises exception
        """
        if function_group.column == '':
            return True
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

    def parse_where_clause(self, where_clause_ast, M_c, T, column_lists): 
        """
        Creates conditions: the list of conditions in the whereclause
        List of (c_idx, op, val)
        """
        conditions = []
        operator_map = {'<=': operator.le, '<': operator.lt, '=': operator.eq,
                        '>': operator.gt, '>=': operator.ge, 'in': operator.contains}

        for single_condition in where_clause_ast:
            ## Confidence in the where clause not yet handled by client/engine. 
            confidence = None
            if single_condition.confidence != '':
                confidence = float(single_condition.confidence)
                
            raw_value = single_condition.value
            function = None
            args = None
            ## SELECT and INFER versions
            if single_condition.function.function_id == 'typicality':
                value = utils.value_string_to_num(raw_value)
                function = functions._row_typicality
                assert self.get_args_typicality(single_condition.function, M_c) == True
                args = True
            elif single_condition.function.function_id == 'similarity':
                value = utils.value_string_to_num(raw_value)
                function = functions._similarity
                args = self.get_args_similarity(single_condition.function, M_c, T, column_lists)
            elif single_condition.function.function_id == 'predictive probability':
                value = utils.value_string_to_num(raw_value)
                function = functions._predictive_probability
                args = self.get_args_pred_prob(single_condition.function, M_c)
            
            elif single_condition.function.function_id == 'key':
                value = raw_value
                function = functions._row_id
            elif single_condition.function.column != '':
                ## whereclause of the form "where col = val" 
                column_name = single_condition.function.column
                assert column_name != '*'
                if column_name in M_c['name_to_idx']:
                    args = M_c['name_to_idx'][column_name]
                    value = utils.string_to_column_type(raw_value, column_name, M_c)
                    function = functions._column
                else:
                    raise utils.BayesDBParseError("Invalid where clause: column %s was not found in the table" % 
                                                  column_name)
            else:
                if single_condition.function.function_id != '':
                    raise utils.BayesDBParseError("Invalid where clause: %s not allowed." % 
                                                  single_condition.function.function_id)
                else: 
                    raise utils.BayesDBParseError("Invalid where clause. Unrecognized function")
            if single_condition.operation != '':
                op = operator_map[single_condition.operation]
            else: 
                raise utils.BayesDBParseError("Invalid where clause: no operator found")
            conditions.append(((function, args), op, value))
        return conditions
    
    def parse_column_whereclause(self, whereclause, M_c, T): ##TODO throw exception on parseable, invalid
        """
        Creates conditions: the list of conditions in the whereclause
        List of (c_idx, op, val)
        """
        conditions = []
        if whereclause == None:
            return conditions
        operator_map = {'<=': operator.le, '<': operator.lt, '=': operator.eq,
                        '>': operator.gt, '>=': operator.ge, 'in': operator.contains}
        
        for single_condition in whereclause:
            ## Confidence in the where clause not yet handled by client/engine. 
            
            raw_value = single_condition.value
            value = utils.value_string_to_num(raw_value)
            function = None
            args = None
            _ = None
            ## SELECT and INFER versions
            if single_condition.function.function_id == 'typicality':
                function = functions._col_typicality
                assert self.get_args_typicality(single_condition.function, M_c) == True
                args = None
            elif single_condition.function.function_id == 'dependence probability':
                function = functions._dependence_probability
                _, args = self.get_args_of_with(single_condition.function, M_c)
            elif single_condition.function.function_id == 'mutual information':
                function = functions._mutual_information
                _, args = self.get_args_of_with(single_condition.function, M_c)
            elif single_condition.function.function_id == 'correlation':
                function = functions._correlation
                _, args = self.get_args_of_with(single_condition.function, M_c)
            else:
                if single_condition.function.function_id != '':
                    raise utils.BayesDBParseError("Invalid where clause: %s not allowed." % 
                                                  single_condition.function.function_id)
                else: 
                    raise utils.BayesDBParseError("Invalid where clause. Unrecognized function")
            if single_condition.operation != '':
                op = operator_map[single_condition.operation]
            else: 
                raise utils.BayesDBParseError("Invalid where clause: no operator found")
            if _ != None:
                raise utils.BayesDBParseError("Invalid where clause, do not specify an 'of' column in estimate columns")
            conditions.append(((function, args), op, value))
        return conditions

    def parse_order_by_clause(self, order_by_clause_ast, M_c, T, column_lists):
        function_list = []
        for orderable in order_by_clause_ast:
            desc = True
            if orderable.asc_desc == 'asc':
                desc = False
            if orderable.function.function_id == 'similarity':
                function = functions._similarity 
                args = self.get_args_similarity(orderable.function, M_c, T, column_lists)
            elif orderable.function.function_id == 'typicality':
                function = functions._row_typicality
                args = self.get_args_typicality(orderable.function, M_c)
            elif orderable.function.function_id == 'predictive probability':
                function = functions._predictive_probability
                args = self.get_args_pred_prob(orderable.function, M_c)
            elif orderable.function.column != '': 
                function = functions._column
                args = M_c['name_to_idx'][orderable.function.column]
            else:
                raise utils.BayesDBParseError("Invalid order by clause.")
            function_list.append((function, args, desc))
        return function_list

    def parse_column_order_by_clause(self, order_by_clause_ast, M_c, ):
        function_list = []
        for orderable in order_by_clause_ast:
            desc = True
            if orderable.asc_desc == 'asc':
                desc = False
            if orderable.function.function_id == 'typicality':
                assert orderable.function.column == '', "BayesDBParseError: Column order by typicality cannot include 'of %s'" % orderable.function.column
                function = functions._col_typicality
                args = None 
            elif orderable.function.function_id == 'dependence probability':
                function = functions._dependence_probability
                _, args = self.get_args_of_with(orderable.function, M_c)
            elif orderable.function.function_id == 'correlation':
                function = functions._correlation
                _, args = self.get_args_of_with(orderable.function, M_c)
            elif orderable.function.function_id == 'mutual information':
                function = functions._mutual_information
                _, args = self.get_args_of_with(orderable.function, M_c)
            else:
                raise utils.BayesDBParseError("Invalid order by clause. Can only order by typicality, correlation, mutual information, or dependence probability.")
            function_list.append((function, args, desc))
        
        return function_list

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

        for function_group in function_groups: 
            if function_group.function_id == 'predictive probability':
                queries.append((functions._predictive_probability, 
                                self.get_args_pred_prob(function_group, M_c), 
                                False))
                query_colnames.append(' '.join(function_group))
            elif function_group.function_id == 'typicality':
                if function_group.column != '':
                    queries.append((functions._col_typicality, 
                                    self.get_args_typicality(function_group, M_c), 
                                    True))
                else:
                    queries.append((functions._row_typicality,
                                    self.get_args_typicality(function_group, M_c), 
                                    False))
                query_colnames.append(' '.join(function_group))
            elif function_group.function_id == 'probability':
                queries.append((functions._probability, 
                                self.get_args_prob(function_group, M_c), 
                                True))
                query_colnames.append(' '.join(function_group))
            elif function_group.function_id == 'similarity':
                assert M_c is not None
                queries.append((functions._similarity, 
                                self.get_args_similarity(function_group, M_c, T, column_lists),
                                False))
                pre_name_list = function_group.asList()
                if function_group.with_respect_to != '':
                    pre_name_list[-1] = ', '.join(pre_name_list[-1])
                query_colnames.append(' '.join(pre_name_list))
            elif function_group.function_id == 'dependence probability':
                queries.append((functions._dependence_probability, 
                                self.get_args_of_with(function_group, M_c), 
                                True))
                query_colnames.append(' '.join(function_group))
            elif function_group.function_id == 'mutual information':
                queries.append((functions._mutual_information, 
                                self.get_args_of_with(function_group, M_c), 
                                True))
                query_colnames.append(' '.join(function_group))
            elif function_group.function_id == 'correlation':
                queries.append((functions._correlation, 
                                self.get_args_of_with(function_group, M_c), 
                                True))
                query_colnames.append(' '.join(function_group))
            ## single column, column_list, or *
            elif function_group.column_id != '':
                column_name = function_group.column_id
                assert M_c is not None
                index_list, name_list = self.parse_column_set(column_name, M_c, column_lists)
                queries += [(functions._column, column_index , False) for column_index in index_list]
                query_colnames += [name for name in name_list]
            else: 
                raise utils.BayesDBParseError("Invalid query: could not parse function")
        return queries, query_colnames

    def parse_column_set(self, column_name, M_c, column_lists = None):
        """
        given a string representation of a column name or column_list,
        returns a list of the column indexes, list of column names. 
        """
        index_list = []
        name_list = []
        if column_name == '*':
            all_columns = utils.get_all_column_names_in_original_order(M_c)
            index_list += [M_c['name_to_idx'][column_name] for column_name in all_columns]
            name_list += [name for name in all_columns]
        elif (column_lists is not None) and (column_name in column_lists.keys()):
            index_list += [M_c['name_to_idx'][name] for name in column_lists[column_name]]
            name_list += [name for name in column_lists[column_name]]
        elif column_name in M_c['name_to_idx']:
            index_list += [M_c['name_to_idx'][column_name]]
            name_list += [column_name]
        else:
            raise utils.BayesDBParseError("Invalid query: %s not found." % column_name)
        return index_list, name_list

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

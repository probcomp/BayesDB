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

import time
import inspect
import pickle
import os
import pytest
from pyparsing import *

from bayesdb.bql_grammar import *
from bayesdb.engine import Engine
from bayesdb.parser import Parser
import bayesdb.functions as functions
import numpy
engine = Engine('local')
parser = Parser()

test_M_c = {'idx_to_name': {'1': 'b', '0': 'a', '3': 'd', '2': 'c'},
            'column_metadata': [
                    {'code_to_value': {'a': 0, '1': 1, '2': 2, '4': 3, '6': 4},
                     'value_to_code': {0: 'a', 1: '1', 2: '2', 3: '4', 4: '6'},
                     'modeltype': 'symmetric_dirichlet_discrete'},
                    {'code_to_value': {}, 'value_to_code': {},
                     'modeltype': 'normal_inverse_gamma'},
                    {'code_to_value': {'we': 0, 'e': 1, 'w': 2, 'sd': 3},
                     'value_to_code': {0: 'we', 1: 'e', 2: 'w', 3: 'sd'},
                     'modeltype': 'symmetric_dirichlet_discrete'},
                    {'code_to_value': {'3': 1, '2': 2, '5': 0, '4': 3},
                     'value_to_code': {0: '5', 1: '3', 2: '2', 3: '4'},
                     'modeltype': 'symmetric_dirichlet_discrete'}],
            'name_to_idx': {'a': 0, 'c': 2, 'b': 1, 'd': 3}}

test_M_c_full = {'idx_to_name': {'1': 'b', '0': 'a', '3': 'd', '2': 'c', '4': 'key'},
            'column_metadata': [
                    {'code_to_value': {'a': 0, '1': 1, '2': 2, '4': 3, '6': 4},
                     'value_to_code': {0: 'a', 1: '1', 2: '2', 3: '4', 4: '6'},
                     'modeltype': 'symmetric_dirichlet_discrete'},
                    {'code_to_value': {}, 'value_to_code': {},
                     'modeltype': 'normal_inverse_gamma'},
                    {'code_to_value': {'we': 0, 'e': 1, 'w': 2, 'sd': 3},
                     'value_to_code': {0: 'we', 1: 'e', 2: 'w', 3: 'sd'},
                     'modeltype': 'symmetric_dirichlet_discrete'},
                    {'code_to_value': {'3': 1, '2': 2, '5': 0, '4': 3},
                     'value_to_code': {0: '5', 1: '3', 2: '2', 3: '4'},
                     'modeltype': 'symmetric_dirichlet_discrete'},
                    {'code_to_value': {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8},
                     'value_to_code': {0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8'},
                     'modeltype': 'ignore'}],
            'name_to_idx': {'a': 0, 'c': 2, 'b': 1, 'd': 3, 'key': 4}}


test_T = [[1.0, 1.0, 0.0, numpy.nan],
          [2.0, 2.0, 0.0, 2.0],
          [0.0, 3.0, 0.0, 3.0],
          [3.0, 3.0, 2.0, numpy.nan],
          [3.0, 4.0, 2.0, 0.0],
          [4.0, 5.0, 1.0, numpy.nan],
          [numpy.nan, 6.0, 2.0, 1.0],
          [numpy.nan, 7.0, 3.0, 1.0],
          [numpy.nan, 7.0, 3.0, 1.0]]

test_T_full = [[1.0, 1.0, 0.0, numpy.nan, 0],
          [2.0, 2.0, 0.0, 2.0, 1],
          [0.0, 3.0, 0.0, 3.0, 2],
          [3.0, 3.0, 2.0, numpy.nan, 3],
          [3.0, 4.0, 2.0, 0.0, 4],
          [4.0, 5.0, 1.0, numpy.nan, 5],
          [numpy.nan, 6.0, 2.0, 1.0, 6],
          [numpy.nan, 7.0, 3.0, 1.0, 7],
          [numpy.nan, 7.0, 3.0, 1.0, 8]]

def test_keyword_plurality_ambiguity_pyparsing():
    model = model_keyword.parseString("model",parseAll=True)
    models = model_keyword.parseString("models",parseAll=True)
    assert model[0] == 'model'
    assert models[0] == 'model'
    iteration = iteration_keyword.parseString("iteration",parseAll=True)
    iterations = iteration_keyword.parseString("iterations",parseAll=True)
    assert iteration[0] == 'iteration'
    assert iterations[0] == 'iteration'
    sample = sample_keyword.parseString("sample",parseAll=True)
    samples = sample_keyword.parseString("samples",parseAll=True)
    assert sample[0] == 'sample'
    assert samples[0] == 'sample'
    column = column_keyword.parseString('column',parseAll=True)
    columns = column_keyword.parseString('columns',parseAll=True)
    assert column[0] == 'column'
    assert columns[0] == 'column'
    list_ = list_keyword.parseString('list',parseAll=True)
    lists = list_keyword.parseString('lists',parseAll=True)
    assert list_[0] == 'list'
    assert lists[0] == 'list'
    btable = btable_keyword.parseString('btable',parseAll=True)
    btables = btable_keyword.parseString('btables',parseAll=True)
    assert btable[0] == 'btable'
    assert btables[0] == 'btable'
    minute = minute_keyword.parseString('minute',parseAll=True)
    minutes = minute_keyword.parseString('minutes',parseAll=True)
    assert minute[0] == 'minute'
    assert minute[0] == 'minute'

def test_composite_keywords_pyparsing():
    execute_file = execute_file_keyword.parseString('eXecute file',parseAll=True)
    assert execute_file[0] == 'execute_file'
    create_btable = create_btable_keyword.parseString('cReate btable',parseAll=True)
    assert create_btable[0] == 'create_btable'
    update_schema_for = update_schema_for_keyword.parseString('update Schema for',parseAll=True)
    assert update_schema_for[0] == 'update_schema'
    models_for = models_for_keyword.parseString('Models for',parseAll=True)
    assert models_for[0] == 'model for'
    model_index = model_index_keyword.parseString('model Index',parseAll=True)
    assert model_index[0] == 'model index'
    save_model = save_model_keyword.parseString("save modeL",parseAll=True)
    assert save_model[0] == 'save_models'
    load_model = load_model_keyword.parseString("load Models",parseAll=True)
    assert load_model[0] == 'load_models'
    save_to = save_to_keyword.parseString('save To',parseAll=True)
    assert save_to[0] == 'save to'
    list_btables = list_btables_keyword.parseString('list bTables',parseAll=True)
    assert list_btables[0] == 'list_btables'
    show_schema_for = show_schema_for_keyword.parseString('show Schema for',parseAll=True)
    assert show_schema_for[0] == 'show_schema'
    show_models_for = show_models_for_keyword.parseString("show modeLs for",parseAll=True)
    assert show_models_for[0] == 'show_models'
    show_diagnostics_for = show_diagnostics_for_keyword.parseString("show diaGnostics for",parseAll=True)
    assert show_diagnostics_for[0] == 'show_diagnostics'
    estimate_pairwise = estimate_pairwise_keyword.parseString("estimate Pairwise",parseAll=True)
    assert estimate_pairwise[0] == 'estimate_pairwise'
    with_confidence = with_confidence_keyword.parseString('with  confIdence',parseAll=True)
    assert with_confidence[0] == 'with confidence'
    dependence_probability = dependence_probability_keyword.parseString('dependence probability',parseAll=True)
    assert dependence_probability[0] == 'dependence probability'
    mutual_information = mutual_information_keyword.parseString('mutual inFormation',parseAll=True)
    assert mutual_information[0] == 'mutual information'
    estimate_columns_from = estimate_columns_from_keyword.parseString("estimate columns froM",parseAll=True)
    assert estimate_columns_from[0] == 'estimate_columns'
    column_lists = column_lists_keyword.parseString('column Lists',parseAll=True)
    assert column_lists[0] == 'column list'
    with_respect_to = with_respect_to_keyword.parseString("with Respect to",parseAll=True)
    assert with_respect_to[0] == 'with respect to'
    probability_of = probability_of_keyword.parseString('probability of',parseAll=True)
    assert probability_of[0] == 'probability'
    predictive_probability_of = predictive_probability_of_keyword.parseString('predictive Probability  of',parseAll=True)
    assert predictive_probability_of[0] == 'predictive probability'
    save_clusters_with_threshold = save_clusters_with_threshold_keyword.parseString(
        'save clusters with threshold',parseAll=True)
    assert save_clusters_with_threshold[0] == 'save clusters with threshold'
    estimate_pairwise_row = estimate_pairwise_row_keyword.parseString("estimate Pairwise row",parseAll=True)
    assert estimate_pairwise_row[0] == 'estimate_pairwise_row'

def test_valid_values_names_pyparsing():
    valid_values=[
        '4',
        '42.04',
        '.4',
        '4.',
        "'\sjekja8391(*^@(%()!@#$%^&*()_+=-~'",
        "a0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+-./:<=>?@[\]^_`{|}~",
        'b0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+-./:<=>?@[\]^_`{|}~',
        '"c0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\\"#$%&\'()*+-./:<=>?@[\]^_`{|}~"',
        "'d0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\\'()*+-./:<=>?@[\]^_`{|}~'",
        "'numbers 0'",
        "'k skj s'",
        ]
    valid_values_results=[
        '4',
        '42.04',
        '.4',
        '4.',
        '\sjekja8391(*^@(%()!@#$%^&*()_+=-~',
        "a0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+-./:<=>?@[\]^_`{|}~",
        'b0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+-./:<=>?@[\]^_`{|}~',
        "c0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+-./:<=>?@[\]^_`{|}~",
        "d0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+-./:<=>?@[\]^_`{|}~",
        'numbers 0',
        'k skj s',
        ]

    for i in range(len(valid_values)):
        assert value.parseString(valid_values[i],parseAll=True)[0] == valid_values_results[i]

    valid_column_identifiers = [
        "a",
        "a1",
        "a_1",
        "a_a",
        "a_",
        "aa"
        ]
    valid_column_identifiers_results = [
        "a",
        "a1",
        "a_1",
        "a_a",
        "a_",
        "aa"
        ]
    for i in range(len(valid_column_identifiers)):
        assert value.parseString(valid_column_identifiers[i],parseAll=True)[0] == valid_column_identifiers_results[i]
    assert float_number.parseString('1',parseAll=True)[0] == '1'
    assert int_number.parseString('1',parseAll=True)[0] == '1'
    assert float_number.parseString('1.')[0] == '1'
    assert float_number.parseString('.1',parseAll=True)[0] == '.1'
    assert float_number.parseString('0.1',parseAll=True)[0] == '0.1'
    assert float_number.parseString('11',parseAll=True)[0] == '11'
    assert int_number.parseString('11',parseAll=True)[0] == '11'
    assert float_number.parseString('11.01',parseAll=True)[0] == '11.01'
    assert filename.parseString("~/filename.csv",parseAll=True)[0] == "~/filename.csv"
    assert filename.parseString("!\"/#$%&'()*+-.:<=>?@[\]^_`{|}~",parseAll=True)[0] == "!\"/#$%&'()*+-.:<=>?@[\]^_`{|}~"
    assert filename.parseString("'/filename with space.csv'",parseAll=True)[0] == "/filename with space.csv"

def test_simple_functions():
    assert list_btables_function.parseString("LIST BTABLES",parseAll=True).statement_id == 'list_btables'
    assert list_btables_function.parseString("LIST BTABLE",parseAll=True).statement_id == 'list_btables'
    assert show_for_btable_statement.parseString("SHOW SCHEMA FOR table_1",parseAll=True).statement_id == 'show_schema'
    assert show_for_btable_statement.parseString("SHOW SCHEMA FOR table_1",parseAll=True).btable == 'table_1'
    assert show_for_btable_statement.parseString("SHOW MODELS FOR table_1",parseAll=True).statement_id == 'show_models'
    assert show_for_btable_statement.parseString("SHOW MODEL FOR table_1",parseAll=True).btable == 'table_1'
    assert show_for_btable_statement.parseString("SHOW DIAGNOSTICS FOR table_1",parseAll=True).statement_id == 'show_diagnostics'
    assert show_for_btable_statement.parseString("SHOW DIAGNOSTICS FOR table_1",parseAll=True).btable == 'table_1'

    assert show_for_btable_statement.parseString("SHOW COLUMN LISTS FOR table_1",parseAll=True).btable == 'table_1'
    assert show_for_btable_statement.parseString("SHOW COLUMNS LIST FOR table_1",parseAll=True).statement_id == 'show_column_lists'
    assert show_columns_function.parseString("SHOW COLUMNS asdf FOR table_1",parseAll=True).column_list == 'asdf'
    assert drop_column_list_function.parseString("DROP COLUMN LIST group1 FROM table_1", parseAll=True).list_name == 'group1'
    assert drop_column_list_function.parseString("DROP COLUMN LIST group1 FROM table_1", parseAll=True).statement_id == 'drop_column_list'
    assert drop_column_list_function.parseString("DROP COLUMN LIST group1 FROM table_1", parseAll=True).btable == 'table_1'
    assert show_for_btable_statement.parseString("SHOW ROW LISTS FOR table_1",parseAll=True).statement_id == 'show_row_lists'
    assert show_for_btable_statement.parseString("SHOW ROW list FOR table_1",parseAll=True).btable == 'table_1'
    assert drop_row_list_function.parseString("DROP ROW LIST group1 FROM table_1", parseAll=True).list_name == 'group1'
    assert drop_row_list_function.parseString("DROP ROW LIST group1 FROM table_1", parseAll=True).statement_id == 'drop_row_list'
    assert drop_row_list_function.parseString("DROP ROW LIST group1 FROM table_1", parseAll=True).btable == 'table_1'
    assert load_model_function.parseString("LOAD MODELS ~/filename.csv INTO table_1",parseAll=True).statement_id == 'load_models'
    assert load_model_function.parseString("LOAD MODEL ~/filename.csv INTO table_1",parseAll=True).statement_id == 'load_models'
    assert load_model_function.parseString("LOAD MODELS ~/filename.csv INTO table_1",parseAll=True).filename == '~/filename.csv'
    assert load_model_function.parseString("LOAD MODELS '~/filena me.csv' INTO table_1",parseAll=True).filename == '~/filena me.csv'
    assert load_model_function.parseString("LOAD MODELS ~/filename.csv INTO table_1",parseAll=True).btable == 'table_1'
    assert save_model_from_function.parseString("SAVE MODEL FROM table_1 to filename.pkl.gz",parseAll=True).btable == 'table_1'
    assert save_model_from_function.parseString("SAVE MODEL FROM table_1 to filename.pkl.gz",parseAll=True).statement_id == 'save_models'
    assert save_model_from_function.parseString("SAVE MODEL FROM table_1 to filename.pkl.gz",parseAll=True).filename == 'filename.pkl.gz'
    assert drop_btable_function.parseString("DROP BTABLE table_1",parseAll=True).statement_id == 'drop_btable'
    assert drop_btable_function.parseString("DROP BTABLES table_1",parseAll=True).statement_id == 'drop_btable'
    assert drop_btable_function.parseString("DROP BTABLE table_1",parseAll=True).btable == 'table_1'
    drop_model_1 = drop_model_function.parseString("DROP MODEL 1 FROM table_1",parseAll=True)
    drop_model_2 = drop_model_function.parseString("DROP MODELS 1-5 FROM table_1",parseAll=True)
    drop_model_3 = drop_model_function.parseString("DROP MODELS 1,2,6-9 FROM table_1",parseAll=True)
    drop_model_4 = drop_model_function.parseString("DROP MODELS 1-5,1-5 FROM table_1",parseAll=True)
    assert drop_model_1.statement_id == 'drop_models'
    assert drop_model_1.btable == 'table_1'
    assert drop_model_1.index_clause.asList() == [1]
    assert drop_model_2.index_clause.asList() == [1,2,3,4,5]
    assert drop_model_3.index_clause.asList() == [1,2,6,7,8,9]
    assert drop_model_4.index_clause.asList() == [1,2,3,4,5]
    assert help_function.parseString("HELp",parseAll=True).statement_id == 'help'

def test_update_schema_pyparsing():
    update_schema_1 = update_schema_for_function.parseString("UPDATE SCHEMA FOR test_btable SET col_1 = Categorical,col_2=numerical , col_3  =  ignore",parseAll=True)
    assert update_schema_1.statement_id == 'update_schema'
    assert update_schema_1.btable == 'test_btable'
    assert update_schema_1.type_clause[0][0] == 'col_1'
    assert update_schema_1.type_clause[0][1] == 'categorical'
    assert update_schema_1.type_clause[1][0] == 'col_2'
    assert update_schema_1.type_clause[1][1] == 'numerical'
    assert update_schema_1.type_clause[2][0] == 'col_3'
    assert update_schema_1.type_clause[2][1] == 'ignore'
    update_schema_2 = update_schema_for_function.parseString("UPDATE SCHEMA FOR test_btable SET col_1 = key",parseAll=True)
    assert update_schema_2.type_clause[0][0] == 'col_1'
    assert update_schema_2.type_clause[0][1] == 'key'
    update_schema_3 = update_schema_for_function.parseString("UPDATE SCHEMA FOR test_btable SET col_1 = categorical(15)", parseAll=True)
    assert update_schema_3.type_clause[0][0] == 'col_1'
    assert update_schema_3.type_clause[0][1] == 'categorical'
    assert update_schema_3.type_clause[0].parameters.cardinality == '15'
    update_schema_4 = update_schema_for_function.parseString("UPDATE SCHEMA FOR test_btable SET col_2 = cyclic(0, 10)", parseAll=True)
    assert update_schema_4.type_clause[0][0] == 'col_2'
    assert update_schema_4.type_clause[0][1] == 'cyclic'
    assert update_schema_4.type_clause[0].parameters.min == '0'
    assert update_schema_4.type_clause[0].parameters.max == '10'

def test_update_codebook_pyparsing():
    bql_string = "UPDATE CODEBOOK FOR test_btable FROM new_codebook.csv"
    update_codebook = update_codebook_for_function.parseString(bql_string)

    assert update_codebook.statement_id == 'update_codebook'
    assert update_codebook.btable == 'test_btable'
    assert update_codebook.filename == 'new_codebook.csv'

def test_describe_pyparsing():
    bql_string = "DESCRIBE col_1 FOR test_btable"
    describe_0 = describe_function.parseString(bql_string)
    bql_string = "DESCRIBE col_1, col_2 FOR test_btable"
    describe_1 = describe_function.parseString(bql_string)

    assert describe_0.statement_id == 'describe'
    assert describe_0.btable == 'test_btable'
    assert 'col_1' in describe_0.columnset.asList()

    assert describe_1.statement_id == 'describe'
    assert describe_1.btable == 'test_btable'
    assert 'col_1' in describe_1.columnset.asList()
    assert 'col_2' in describe_1.columnset.asList()

def test_update_descriptions_pyparsing():
    bql_string = 'UPDATE DESCRIPTION FOR test_btable SET col_1="Hamish the cat"'
    updated_description_0 = update_descriptions_for_function.parseString(bql_string)

    assert updated_description_0.statement_id == "update_descriptions"
    assert updated_description_0.btable == "test_btable"
    assert updated_description_0.label_clause[0][0] == "col_1"
    assert updated_description_0.label_clause[0][1] == "Hamish the cat"

    bql_string = 'UPDATE DESCRIPTIONS FOR test_btable SET col_1="Hamish the cat", col_2="trevor"'
    updated_description_1 = update_descriptions_for_function.parseString(bql_string)

    assert updated_description_1.statement_id == "update_descriptions"
    assert updated_description_1.btable == "test_btable"
    assert updated_description_1.label_clause[0][0] == "col_1"
    assert updated_description_1.label_clause[0][1] == "Hamish the cat"
    assert updated_description_1.label_clause[1][0] == "col_2"
    assert updated_description_1.label_clause[1][1] == "trevor"

def test_update_short_names_pyparsing():
    bql_string = 'UPDATE SHORT NAME FOR test_btable SET col_1="Hamish"'
    updated_short_names_0 = update_short_names_for_function.parseString(bql_string)

    assert updated_short_names_0.statement_id == "update_short_names"
    assert updated_short_names_0.btable == "test_btable"
    assert updated_short_names_0.label_clause[0][0] == "col_1"
    assert updated_short_names_0.label_clause[0][1] == "Hamish"

    bql_string = 'UPDATE SHORT NAMES FOR test_btable SET col_1="Hamish", col_2="trevor"'
    updated_short_names_1 = update_short_names_for_function.parseString(bql_string)

    assert updated_short_names_1.statement_id == "update_short_names"
    assert updated_short_names_1.btable == "test_btable"
    assert updated_short_names_1.label_clause[0][0] == "col_1"
    assert updated_short_names_1.label_clause[0][1] == "Hamish"
    assert updated_short_names_1.label_clause[1][0] == "col_2"
    assert updated_short_names_1.label_clause[1][1] == "trevor"

def test_create_btable_pyparsing():
    create_btable_1 = create_btable_function.parseString("CREATE BTABLE test.btable FROM '~/filenam e.csv'", parseAll=True)
    create_btable_2 = create_btable_function.parseString("CREATE BTABLE test_btable FROM ~/filename.csv", parseAll=True)
    assert create_btable_1.statement_id == 'create_btable'
    assert create_btable_1.btable == 'test.btable'
    assert create_btable_1.filename == '~/filenam e.csv'
    assert create_btable_2.btable == 'test_btable'
    assert create_btable_2.filename == '~/filename.csv'

def test_execute_file_pyparsing():
    execute_file_1 = execute_file_function.parseString("EXECUTE FILE '/filenam e.bql'",parseAll=True)
    execute_file_2 = execute_file_function.parseString("EXECUTE FILE /filename.bql",parseAll=True)
    assert execute_file_1.filename == "/filenam e.bql"
    assert execute_file_2.filename == "/filename.bql"

def test_initialize_pyparsing():
    initialize_1 = initialize_function.parseString("INITIALIZE 3 MODELS FOR test_table",parseAll=True)
    assert initialize_1.statement_id == 'initialize_models'
    assert initialize_1.num_models == '3'
    assert initialize_1.btable == 'test_table'
    initialize_2 = initialize_function.parseString("INITIALIZE 3 MODEL FOR test_table",parseAll=True)
    assert initialize_2.statement_id == 'initialize_models'
    assert initialize_2.num_models == '3'
    assert initialize_2.btable == 'test_table'
    initialize_3 = initialize_function.parseString("INITIALIZE MODELS FOR test_table",parseAll=True)
    assert initialize_3.statement_id == 'initialize_models'
    assert initialize_3.num_models == ''
    assert initialize_3.btable == 'test_table'

def test_analyze_pyparsing():
    analyze_1 = analyze_function.parseString("ANALYZE table_1 FOR 10 ITERATIONS",parseAll=True)
    analyze_2 = analyze_function.parseString("ANALYZE table_1 FOR 1 ITERATION",parseAll=True)
    analyze_3 = analyze_function.parseString("ANALYZE table_1 FOR 10 MINUTES",parseAll=True)
    analyze_4 = analyze_function.parseString("ANALYZE table_1 FOR 1 MINUTE",parseAll=True)
    analyze_5 = analyze_function.parseString("ANALYZE table_1 MODEL 1 FOR 10 MINUTES",parseAll=True)
    analyze_6 = analyze_function.parseString("ANALYZE table_1 MODELS 1-3 FOR 1 ITERATION",parseAll=True)
    analyze_7 = analyze_function.parseString("ANALYZE table_1 MODELS 1,2,3 FOR 10 MINUTES",parseAll=True)
    analyze_8 = analyze_function.parseString("ANALYZE table_1 MODELS 1, 3-5 FOR 1 ITERATION",parseAll=True)
    analyze_9 = analyze_function.parseString("ANALYZE table_1 MODELS 1-3, 5 FOR 10 MINUTES",parseAll=True)
    analyze_10 = analyze_function.parseString("ANALYZE table_1 MODELS 1-3, 5-7, 9, 10 FOR 1 ITERATION",parseAll=True)
    analyze_11 = analyze_function.parseString("ANALYZE table_1 MODELS 1, 1, 2, 2 FOR 10 MINUTES",parseAll=True)
    analyze_12 = analyze_function.parseString("ANALYZE table_1 MODELS 1-5, 1-5, 5 FOR 1 ITERATION",parseAll=True)
    assert analyze_1.statement_id == 'analyze'
    assert analyze_1.btable == 'table_1'
    assert analyze_1.index_lust == ''
    assert analyze_1.index_clause == ''
    assert analyze_1.num_iterations == '10'
    assert analyze_1.num_minutes == ''
    assert analyze_2.num_iterations == '1'
    assert analyze_2.num_minutes == ''
    assert analyze_3.num_iterations == ''
    assert analyze_3.num_minutes == '10'
    assert analyze_4.num_iterations == ''
    assert analyze_4.num_minutes == '1'
    assert analyze_5.index_clause.asList() == [1]
    assert analyze_6.index_clause.asList() == [1,2,3]
    assert analyze_7.index_clause.asList() == [1,2,3]
    assert analyze_8.index_clause.asList() == [1,3,4,5]
    assert analyze_9.index_clause.asList() == [1,2,3,5]
    assert analyze_10.index_clause.asList() == [1,2,3,5,6,7,9,10]
    assert analyze_11.index_clause.asList() == [1,2]
    assert analyze_12.index_clause.asList() == [1,2,3,4,5]

def test_subclauses_pyparsing():
    assert save_to_clause.parseString("save to filename.csv").filename == 'filename.csv'

def test_row_clause_pyparsing():
    row_1 = row_clause.parseString('1', parseAll=True)
    row_2 = row_clause.parseString("column = 1", parseAll=True)
    row_3 = row_clause.parseString("column = 'value'", parseAll=True)
    row_4 = row_clause.parseString("column = value", parseAll=True)
    assert row_1.row_id == '1'
    assert row_1.column == ''
    assert row_2.row_id == ''
    assert row_2.column == 'column'
    assert row_2.column_value == '1'
    assert row_3.column_value == 'value'
    assert row_4.column_value == 'value'

def test_row_functions_pyparsing():
    similarity_1 = similarity_to_function.parseString("SIMILARITY TO 1",
                                                      parseAll=True)
    similarity_2 = similarity_to_function.parseString("SIMILARITY TO col_2 = 1",
                                                      parseAll=True)
    similarity_3 = similarity_to_function.parseString("SIMILARITY TO col_2 = 'a'",
                                                      parseAll=True)
    similarity_4 = similarity_to_function.parseString("SIMILARITY TO col_2 = a",
                                                      parseAll=True)
    similarity_5 = similarity_to_function.parseString("SIMILARITY TO 1 WITH RESPECT TO col_1",
                                                      parseAll=True)
    similarity_6 = similarity_to_function.parseString("SIMILARITY TO col_2 = 1 WITH RESPECT TO col_1,col_2",
                                                      parseAll=True)
    similarity_7 = similarity_to_function.parseString("SIMILARITY TO col_2 = 'a' WITH RESPECT TO col_1 , col_3",
                                                      parseAll=True)
    similarity_8 = similarity_to_function.parseString("SIMILARITY TO col_2 = a WITH RESPECT TO col_1",
                                                      parseAll=True)
    assert similarity_1.function.function_id == 'similarity'
    assert similarity_1.function.row_id == '1'
    assert similarity_2.function.column == 'col_2'
    assert similarity_2.function.column_value == '1'
    assert similarity_3.function.column == 'col_2'
    assert similarity_3.function.column_value == 'a'
    assert similarity_4.function.column == 'col_2'
    assert similarity_4.function.column_value == 'a'
    assert similarity_4.function.with_respect_to == ''
    assert not similarity_5.function.with_respect_to == ''
    assert similarity_5.function.column_list.asList() == ['col_1']
    assert similarity_6.function.column_list.asList() == ['col_1', 'col_2']
    assert similarity_7.function.column_list.asList() == ['col_1', 'col_3']
    assert similarity_8.function.column_list.asList() == ['col_1']
    assert typicality_function.parseString('Typicality',parseAll=True).function.function_id == 'typicality'

def test_column_functions_pyparsing():
    dependence_1 = dependence_probability_function.parseString('DEPENDENCE PROBABILITY WITH column_1',
                                                                    parseAll=True)
    dependence_2 = dependence_probability_function.parseString('DEPENDENCE PROBABILITY OF column_2 WITH column_1',
                                                                    parseAll=True)
    assert dependence_1.function.function_id == 'dependence probability'
    assert dependence_2.function.function_id == 'dependence probability'
    assert dependence_1.function.with_column == 'column_1'
    assert dependence_2.function.with_column == 'column_1'
    assert dependence_2.function.of_column == 'column_2'
    mutual_1 = mutual_information_function.parseString('MUTUAL INFORMATION WITH column_1',
                                                                    parseAll=True)
    mutual_2 = mutual_information_function.parseString('MUTUAL INFORMATION OF column_2 WITH column_1',
                                                                    parseAll=True)
    assert mutual_1.function.function_id == 'mutual information'
    assert mutual_2.function.function_id == 'mutual information'
    assert mutual_1.function.with_column == 'column_1'
    assert mutual_2.function.with_column == 'column_1'
    assert mutual_2.function.of_column == 'column_2'
    correlation_1 = correlation_function.parseString('CORRELATION WITH column_1',
                                                                    parseAll=True)
    correlation_2 = correlation_function.parseString('CORRELATION OF column_2 WITH column_1',
                                                                    parseAll=True)
    assert correlation_1.function.function_id == 'correlation'
    assert correlation_2.function.function_id == 'correlation'
    assert correlation_1.function.with_column == 'column_1'
    assert correlation_2.function.with_column == 'column_1'
    assert correlation_2.function.of_column == 'column_2'


def test_probability_of_function_pyparsing():
    probability_of_1 = probability_of_function.parseString("PROBABILITY OF col_1 = 1",parseAll=True)
    probability_of_2 = probability_of_function.parseString("PROBABILITY OF col_1 = 'value'",parseAll=True)
    probability_of_3 = probability_of_function.parseString("PROBABILITY OF col_1 = value",parseAll=True)
    assert probability_of_1.function.function_id == 'probability'
    assert probability_of_1.function.column == 'col_1'
    assert probability_of_1.function.value == '1'
    assert probability_of_2.function.value == 'value'
    assert probability_of_3.function.value == 'value'

def test_predictive_probability_of_pyparsing():
    assert predictive_probability_of_function.parseString("PREDICTIVE PROBABILITY OF column_1",
                                                          parseAll=True).function.function_id == 'predictive probability'
    assert predictive_probability_of_function.parseString("PREDICTIVE PROBABILITY OF column_1",
                                                          parseAll=True).function.column == 'column_1'

def test_typicality_of_pyparsing():
    assert typicality_function.parseString("TYPICALITY OF column_1",
                                                          parseAll=True).function.function_id == 'typicality'
    assert typicality_function.parseString("TYPICALITY OF column_1",
                                                          parseAll=True).function.column == 'column_1'

def test_order_by_clause_pyparsing():
    order_by_1 = order_by_clause.parseString("ORDER BY column_1"
                                             ,parseAll=True)
    order_by_2 = order_by_clause.parseString("ORDER BY column_1,column_2 , column_3"
                                             ,parseAll=True)
    assert order_by_1.order_by[0].function.column == 'column_1'
    assert order_by_2.order_by[1].function.column =='column_2'
    order_by_3 = order_by_clause.parseString("ORDER BY TYPICALITY",
                                             parseAll=True)
    assert order_by_3.order_by[0].function.function_id == 'typicality'
    order_by_4 = order_by_clause.parseString("ORDER BY TYPICALITY, column_1",
                                             parseAll=True)
    assert order_by_4.order_by[0].function.function_id == 'typicality'
    assert order_by_4.order_by[1].function.column == 'column_1'
    order_by_5 = order_by_clause.parseString("ORDER BY column_1, TYPICALITY",
                                             parseAll=True)
    assert order_by_5.order_by[0].function.column == 'column_1'
    assert order_by_5.order_by[1].function.function_id == 'typicality'
    order_by_6 = order_by_clause.parseString("ORDER BY PREDICTIVE PROBABILITY OF column_1",
                                             parseAll=True)
    assert order_by_6.order_by[0].function.function_id == 'predictive probability'
    assert order_by_6.order_by[0].function.column == 'column_1'

    order_by_7 = order_by_clause.parseString("ORDER BY PREDICTIVE PROBABILITY OF column_1, column_1",
                                             parseAll=True)
    assert order_by_7.order_by[1].function.column == 'column_1'
    assert order_by_7.order_by[0].function.function_id == 'predictive probability'
    assert order_by_7.order_by[0].function.column == 'column_1'

    order_by_8 = order_by_clause.parseString("ORDER BY column_1, TYPICALITY, PREDICTIVE PROBABILITY OF column_1, column_2, SIMILARITY TO 2, SIMILARITY TO column_1 = 1 WITH RESPECT TO column_4",
                                             parseAll=True)
    assert order_by_8.order_by[0].function.column == 'column_1'
    assert order_by_8.order_by[1].function.function_id == 'typicality'
    assert order_by_8.order_by[2].function.function_id == 'predictive probability'
    assert order_by_8.order_by[2].function.column == 'column_1'
    assert order_by_8.order_by[3].function.column == 'column_2'
    assert order_by_8.order_by[4].function.function_id == 'similarity'
    assert order_by_8.order_by[4].function.row_id == '2'
    assert order_by_8.order_by[5].function.function_id == 'similarity'
    assert order_by_8.order_by[5].function.column == 'column_1'
    assert order_by_8.order_by[5].function.column_value == '1'
    assert order_by_8.order_by[5].function.with_respect_to[1][0] == 'column_4' #todo names instead of indexes

    order_by_9 = order_by_clause.parseString("ORDER BY column_1 asc"
                                             ,parseAll=True)
    order_by_10 = order_by_clause.parseString("ORDER BY column_1 asc,column_2 desc , column_3"
                                             ,parseAll=True)
    assert order_by_9.order_by[0].function.column =='column_1'
    assert order_by_10.order_by[1].function.column =='column_2'
    assert order_by_9.order_by[0].asc_desc =='asc'
    assert order_by_10.order_by[1].asc_desc =='desc'
    order_by_11 = order_by_clause.parseString("ORDER BY TYPICALITY asc",
                                             parseAll=True)
    assert order_by_11.order_by[0].asc_desc =='asc'

def test_whereclause_pyparsing():
    # WHERE <column> <operation> <value>
    whereclause_1 = "WHERE column_1 = 1"
    parsed_1 = where_clause.parseString(whereclause_1,parseAll=True)
    assert parsed_1.where_keyword == 'where'
    assert parsed_1.where_conditions[0].function.column == 'column_1'
    assert parsed_1.where_conditions[0].operation == '='
    assert parsed_1.where_conditions[0].value == '1'
    whereclause_2 = "WHERE column_1 <= 1"
    parsed_2 = where_clause.parseString(whereclause_2,parseAll=True)
    assert parsed_2.where_conditions[0].function.column == 'column_1'
    assert parsed_2.where_conditions[0].operation == '<='
    assert parsed_2.where_conditions[0].value == '1'
    whereclause_3 = "WHERE column_1 > 1.0"
    parsed_3 = where_clause.parseString(whereclause_3,parseAll=True)
    assert parsed_3.where_conditions[0].operation == '>'
    assert parsed_3.where_conditions[0].value == '1.0'
    whereclause_4 = "WHERE column_1 = a"
    parsed_4 = where_clause.parseString(whereclause_4,parseAll=True)
    assert parsed_4.where_conditions[0].operation == '='
    assert parsed_4.where_conditions[0].value == 'a'
    whereclause_5 = "WHERE column_1 = 'a'"
    parsed_5 = where_clause.parseString(whereclause_5,parseAll=True)
    assert parsed_5.where_conditions[0].value == 'a'
    whereclause_6 = "WHERE column_1 = 'two words'"
    parsed_6 = where_clause.parseString(whereclause_6,parseAll=True)
    assert parsed_6.where_conditions[0].value == 'two words'
    # Functions
    whereclause_7 = "WHERE TYPICALITY > .8"
    parsed_7 = where_clause.parseString(whereclause_7,parseAll=True)
    assert parsed_7.where_conditions[0].function.function_id == 'typicality'
    assert parsed_7.where_conditions[0].operation == '>'
    assert parsed_7.where_conditions[0].value == '.8'
    whereclause_8 = "WHERE PREDICTIVE PROBABILITY OF column_1 > .1"
    parsed_8 = where_clause.parseString(whereclause_8,parseAll=True)
    assert parsed_8.where_conditions[0].function.function_id == 'predictive probability'
    assert parsed_8.where_conditions[0].function.column == 'column_1'
    assert parsed_8.where_conditions[0].operation == '>'
    assert parsed_8.where_conditions[0].value == '.1'
    whereclause_9 = "WHERE SIMILARITY TO 2 > .1"
    parsed_9 = where_clause.parseString(whereclause_9,parseAll=True)
    assert parsed_9.where_conditions[0].function.function_id == 'similarity'
    assert parsed_9.where_conditions[0].function.row_id == '2'
    assert parsed_9.where_conditions[0].operation == '>'
    assert parsed_9.where_conditions[0].value == '.1'
    whereclause_10 = "WHERE SIMILARITY TO 2 WITH RESPECT TO column_1 > .4"
    parsed_10 = where_clause.parseString(whereclause_10,parseAll=True)
    assert parsed_10.where_conditions[0].function.function_id == 'similarity'
    assert parsed_10.where_conditions[0].function.row_id == '2'
    assert parsed_10.where_conditions[0].function.with_respect_to.column_list[0] == 'column_1'
    assert parsed_10.where_conditions[0].operation == '>'
    assert parsed_10.where_conditions[0].value == '.4'
    whereclause_11 = "WHERE SIMILARITY TO column_1 = 1 = .5"
    parsed_11 = where_clause.parseString(whereclause_11,parseAll=True)
    assert parsed_11.where_conditions[0].function.function_id == 'similarity'
    assert parsed_11.where_conditions[0].function.column == 'column_1'
    assert parsed_11.where_conditions[0].function.column_value == '1'
    assert parsed_11.where_conditions[0].operation == '='
    assert parsed_11.where_conditions[0].value == '.5'
    whereclause_12 = "WHERE SIMILARITY TO column_1 = 'a' WITH RESPECT TO column_2 > .5"
    parsed_12 = where_clause.parseString(whereclause_12,parseAll=True)
    assert parsed_12.where_conditions[0].function.function_id == 'similarity'
    assert parsed_12.where_conditions[0].function.column == 'column_1'
    assert parsed_12.where_conditions[0].function.column_value == 'a'
    assert parsed_12.where_conditions[0].operation == '>'
    assert parsed_12.where_conditions[0].value == '.5'
    assert parsed_12.where_conditions[0].function.with_respect_to.column_list[0] == 'column_2'
    whereclause_13 = "WHERE SIMILARITY TO column_1 = 1.2 WITH RESPECT TO column_2 > .5"
    parsed_13 = where_clause.parseString(whereclause_13,parseAll=True)
    assert parsed_13.where_conditions[0].function.function_id == 'similarity'
    assert parsed_13.where_conditions[0].function.column == 'column_1'
    assert parsed_13.where_conditions[0].function.column_value == '1.2'
    assert parsed_13.where_conditions[0].operation == '>'
    assert parsed_13.where_conditions[0].value == '.5'
    assert parsed_13.where_conditions[0].function.with_respect_to.column_list[0] == 'column_2'
    whereclause_14 = "WHERE SIMILARITY TO column_1 = a WITH RESPECT TO column_2 > .5"
    parsed_14 = where_clause.parseString(whereclause_14,parseAll=True)
    assert parsed_14.where_conditions[0].function.function_id == 'similarity'
    assert parsed_14.where_conditions[0].function.column == 'column_1'
    assert parsed_14.where_conditions[0].function.column_value == 'a'
    assert parsed_14.where_conditions[0].operation == '>'
    assert parsed_14.where_conditions[0].value == '.5'
    assert parsed_14.where_conditions[0].function.with_respect_to.column_list[0] == 'column_2'
    # With Confidence
    whereclause_15 = "WHERE TYPICALITY > .8 CONF .5"
    parsed_15 = where_clause.parseString(whereclause_15,parseAll=True)
    assert parsed_15.where_conditions[0].conf == '.5'
    whereclause_16 = "WHERE PREDICTIVE PROBABILITY OF column_1 > .1 CONF .5"
    parsed_16 = where_clause.parseString(whereclause_16,parseAll=True)
    assert parsed_16.where_conditions[0].conf == '.5'
    whereclause_17 = "WHERE SIMILARITY TO 2 > .1 CONF .5"
    parsed_17 = where_clause.parseString(whereclause_17,parseAll=True)
    assert parsed_17.where_conditions[0].conf == '.5'
    whereclause_18 = "WHERE SIMILARITY TO 2 WITH RESPECT TO column_1 > .4 CONF .5"
    parsed_18 = where_clause.parseString(whereclause_18,parseAll=True)
    assert parsed_18.where_conditions[0].conf == '.5'
    whereclause_19 = "WHERE SIMILARITY TO column_1 = 1 = .5 CONF .5"
    parsed_19 = where_clause.parseString(whereclause_19,parseAll=True)
    assert parsed_19.where_conditions[0].conf == '.5'
    whereclause_20 = "WHERE SIMILARITY TO column_1 = 'a' WITH RESPECT TO column_2 > .5 CONF .5"
    parsed_20 = where_clause.parseString(whereclause_20,parseAll=True)
    assert parsed_20.where_conditions[0].conf == '.5'
    whereclause_21 = "WHERE SIMILARITY TO column_1 = 1.2 WITH RESPECT TO column_2 > .5 CONF .5"
    parsed_21 = where_clause.parseString(whereclause_21,parseAll=True)
    assert parsed_21.where_conditions[0].conf == '.5'
    whereclause_22 = "WHERE SIMILARITY TO column_1 = a WITH RESPECT TO column_2 > .5 CONF .5"
    parsed_22 = where_clause.parseString(whereclause_22,parseAll=True)
    assert parsed_22.where_conditions[0].conf == '.5'
    # AND
    whereclause_23 = "WHERE column_1 = 'a' AND column_2 >= 3"
    parsed_23 = where_clause.parseString(whereclause_23,parseAll=True)
    assert parsed_23.where_conditions[0].function.column == 'column_1'
    assert parsed_23.where_conditions[1].function.column == 'column_2'
    whereclause_24 = "WHERE TYPICALITY > .8 AND PREDICTIVE PROBABILITY OF column_1 > .1 AND SIMILARITY TO 2 > .1"
    parsed_24 = where_clause.parseString(whereclause_24,parseAll=True)
    assert parsed_24.where_conditions[0].function.function_id == 'typicality'
    assert parsed_24.where_conditions[1].function.function_id == 'predictive probability'
    assert parsed_24.where_conditions[2].function.function_id == 'similarity'
    whereclause_25 = "WHERE TYPICALITY > .8 CONF .4 AND PREDICTIVE PROBABILITY OF column_1 > .1 CONF .6 AND SIMILARITY TO 2 > .1 CONF .5"
    parsed_25 = where_clause.parseString(whereclause_25,parseAll=True)
    assert parsed_25.where_conditions[0].conf == '.4'
    assert parsed_25.where_conditions[1].conf == '.6'
    assert parsed_25.where_conditions[2].conf == '.5'
    whereclause_26 = "WHERE KEY IN row_list_1 AND column_1 = 'a' AND TYPICALITY > .4"
    parsed_26 = where_clause.parseString(whereclause_26,parseAll=True)
    assert parsed_26.where_conditions[0].function.function_id == 'key'
    assert parsed_26.where_conditions[0].value == 'row_list_1'
    assert parsed_26.where_conditions[1].function.column == 'column_1'
    assert parsed_26.where_conditions[2].function.function_id == 'typicality'

def test_key_in_rowlist():
    assert key_in_rowlist_clause.parseString("key in row_list_1",parseAll=True).function.function_id == "key"
    assert key_in_rowlist_clause.parseString("key in row_list_1",parseAll=True).value == "row_list_1"

def test_basic_select_pyparsing():
    select_1 = "SELECT * FROM table_1"
    select_1_parse = query.parseString(select_1,parseAll=True)
    assert select_1_parse.statement_id == 'select'
    assert select_1_parse.btable == 'table_1'
    assert select_1_parse.functions[0].column_id == '*'
    select_2 = "SELECT column_1,column_3 FROM table_1"
    select_2_parse = query.parseString(select_2,parseAll=True)
    assert select_2_parse.functions[0].column_id == 'column_1'
    assert select_2_parse.functions[1].column_id == 'column_3'
    select_3 = "PLOT SELECT column_1 FROM table_1 WHERE column_2 = 3"
    select_3_parse = query.parseString(select_3,parseAll=True)
    assert select_3_parse.plot == 'plot'
    assert select_3_parse.functions[0].column_id == 'column_1'
    assert select_3_parse.where_keyword == 'where'
    assert select_3_parse.where_conditions[0].value == '3'
    assert select_3_parse.where_conditions[0].function.column == 'column_2'
    assert select_3_parse.where_conditions[0].operation == '='
    select_4 = "SELECT col_1 FROM table_1 ORDER BY TYPICALITY LIMIT 10 SAVE TO ~/test.txt"
    select_4_parse = query.parseString(select_4,parseAll=True)
    assert select_4_parse.functions[0].column_id == 'col_1'
    assert select_4_parse.order_by[0].function.function_id == 'typicality'
    assert select_4_parse.limit == '10'
    assert select_4_parse.filename == '~/test.txt'

def test_select_functions_pyparsing():
    query_1 = "SELECT TYPICALITY FROM table_1"
    query_2 = "SELECT TYPICALITY OF column_1 FROM table_1"
    query_3 = "SELECT PREDICTIVE PROBABILITY OF column_1 FROM table_1"
    query_4 = "SELECT PROBABILITY OF column_1 = 4 FROM table_1"
    query_5 = "SELECT SIMILARITY TO 0 FROM table_1"
    query_5 = "SELECT SIMILARITY TO column_1 = 4 FROM table_1"
    query_6 = "SELECT DEPENDENCE PROBABILITY WITH column_1 FROM table_1"
    query_7 = "SELECT MUTUAL INFORMATION OF column_1 WITH column_2 FROM table_1"
    query_8 = "SELECT CORRELATION OF column_1 WITH column_2 FROM table_1"
    query_9 = "SELECT TYPICALITY, PREDICTIVE PROBABILITY OF column_1 FROM table_1"
    select_ast_1 = query.parseString(query_1,parseAll=True)
    select_ast_2 = query.parseString(query_2,parseAll=True)
    select_ast_3 = query.parseString(query_3,parseAll=True)
    select_ast_4 = query.parseString(query_4,parseAll=True)
    select_ast_5 = query.parseString(query_5,parseAll=True)
    select_ast_6 = query.parseString(query_6,parseAll=True)
    select_ast_7 = query.parseString(query_7,parseAll=True)
    select_ast_8 = query.parseString(query_8,parseAll=True)
    select_ast_9 = query.parseString(query_9,parseAll=True)
    assert select_ast_1.statement_id == 'select'
    assert select_ast_2.statement_id == 'select'
    assert select_ast_3.statement_id == 'select'
    assert select_ast_4.statement_id == 'select'
    assert select_ast_5.statement_id == 'select'
    assert select_ast_5.statement_id == 'select'
    assert select_ast_6.statement_id == 'select'
    assert select_ast_7.statement_id == 'select'
    assert select_ast_8.statement_id == 'select'
    assert select_ast_9.statement_id == 'select'
    assert select_ast_1.functions[0].function_id == 'typicality'
    assert select_ast_2.functions[0].function_id == 'typicality'
    assert select_ast_3.functions[0].function_id == 'predictive probability'
    assert select_ast_4.functions[0].function_id == 'probability'
    assert select_ast_5.functions[0].function_id == 'similarity'
    assert select_ast_5.functions[0].function_id == 'similarity'
    assert select_ast_6.functions[0].function_id == 'dependence probability'
    assert select_ast_7.functions[0].function_id == 'mutual information'
    assert select_ast_8.functions[0].function_id == 'correlation'
    assert select_ast_9.functions[0].function_id == 'typicality'
    assert select_ast_9.functions[1].function_id == 'predictive probability'

def test_infer_pyparsing():
    infer_1 = "INFER * FROM table_1"
    infer_1_parse = query.parseString(infer_1,parseAll=True)
    assert infer_1_parse.statement_id == 'infer'
    assert infer_1_parse.btable == 'table_1'
    assert infer_1_parse.functions[0].column_id == '*'
    infer_2 = "infer column_1,column_3 FROM table_1"
    infer_2_parse = query.parseString(infer_2,parseAll=True)
    assert infer_2_parse.functions[0].column_id == 'column_1'
    assert infer_2_parse.functions[1].column_id == 'column_3'
    infer_3 = "SUMMARIZE infer column_1 FROM table_1 WHERE column_2 = 3"
    infer_3_parse = query.parseString(infer_3,parseAll=True)
    assert infer_3_parse.summarize == 'summarize'
    assert infer_3_parse.functions[0].column_id == 'column_1'
    assert infer_3_parse.where_keyword == 'where'
    assert infer_3_parse.where_conditions[0].value == '3'
    assert infer_3_parse.where_conditions[0].function.column == 'column_2'
    assert infer_3_parse.where_conditions[0].operation == '='
    infer_4 = "infer col_1 FROM table_1 ORDER BY TYPICALITY LIMIT 10 SAVE TO ~/test.txt"
    infer_4_parse = query.parseString(infer_4,parseAll=True)
    assert infer_4_parse.functions[0].column_id == 'col_1'
    assert infer_4_parse.order_by[0].function.function_id == 'typicality'
    assert infer_4_parse.limit == '10'
    assert infer_4_parse.filename == '~/test.txt'
    query_1 = "INFER TYPICALITY FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_2 = "INFER TYPICALITY OF column_1 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_3 = "INFER PREDICTIVE PROBABILITY OF column_1 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_4 = "INFER PROBABILITY OF column_1 = 4 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_5 = "INFER SIMILARITY TO 0 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_5 = "INFER SIMILARITY TO column_1 = 4 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_6 = "INFER DEPENDENCE PROBABILITY WITH column_1 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_7 = "INFER MUTUAL INFORMATION OF column_1 WITH column_2 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_8 = "INFER CORRELATION OF column_1 WITH column_2 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    query_9 = "INFER TYPICALITY, PREDICTIVE PROBABILITY OF column_1 FROM table_1 WITH CONFIDENCE .4 WITH 4 SAMPLES"
    infer_ast_1 = query.parseString(query_1,parseAll=True)
    infer_ast_2 = query.parseString(query_2,parseAll=True)
    infer_ast_3 = query.parseString(query_3,parseAll=True)
    infer_ast_4 = query.parseString(query_4,parseAll=True)
    infer_ast_5 = query.parseString(query_5,parseAll=True)
    infer_ast_6 = query.parseString(query_6,parseAll=True)
    infer_ast_7 = query.parseString(query_7,parseAll=True)
    infer_ast_8 = query.parseString(query_8,parseAll=True)
    infer_ast_9 = query.parseString(query_9,parseAll=True)
    assert infer_ast_1.statement_id == 'infer'
    assert infer_ast_2.statement_id == 'infer'
    assert infer_ast_3.statement_id == 'infer'
    assert infer_ast_4.statement_id == 'infer'
    assert infer_ast_5.statement_id == 'infer'
    assert infer_ast_5.statement_id == 'infer'
    assert infer_ast_6.statement_id == 'infer'
    assert infer_ast_7.statement_id == 'infer'
    assert infer_ast_8.statement_id == 'infer'
    assert infer_ast_9.statement_id == 'infer'
    assert infer_ast_1.functions[0].function_id == 'typicality'
    assert infer_ast_2.functions[0].function_id == 'typicality'
    assert infer_ast_3.functions[0].function_id == 'predictive probability'
    assert infer_ast_4.functions[0].function_id == 'probability'
    assert infer_ast_5.functions[0].function_id == 'similarity'
    assert infer_ast_5.functions[0].function_id == 'similarity'
    assert infer_ast_6.functions[0].function_id == 'dependence probability'
    assert infer_ast_7.functions[0].function_id == 'mutual information'
    assert infer_ast_8.functions[0].function_id == 'correlation'
    assert infer_ast_9.functions[0].function_id == 'typicality'
    assert infer_ast_9.functions[1].function_id == 'predictive probability'
    assert infer_ast_1.samples == '4'
    assert infer_ast_1.confidence == '.4'
    assert infer_ast_2.samples == '4'
    assert infer_ast_2.confidence == '.4'
    assert infer_ast_3.samples == '4'
    assert infer_ast_3.confidence == '.4'
    assert infer_ast_4.samples == '4'
    assert infer_ast_4.confidence == '.4'
    assert infer_ast_5.samples == '4'
    assert infer_ast_5.confidence == '.4'
    assert infer_ast_6.samples == '4'
    assert infer_ast_6.confidence == '.4'
    assert infer_ast_7.samples == '4'
    assert infer_ast_7.confidence == '.4'
    assert infer_ast_8.samples == '4'
    assert infer_ast_8.confidence == '.4'
    assert infer_ast_9.samples == '4'
    assert infer_ast_9.confidence == '.4'

def test_simulate_pyparsing():
    query_1 = "SIMULATE * FROM table_1 WHERE column_1 = 4 TIMES 4 SAVE TO ~/test.csv"
    simulate_ast = query.parseString(query_1,parseAll=True)
    assert simulate_ast.statement_id == 'simulate'
    assert simulate_ast.functions[0].column_id == '*'
    assert simulate_ast.where_keyword == 'where'
    assert simulate_ast.times == '4'
    assert simulate_ast.filename == '~/test.csv'
    query_2 = "SIMULATE col1,col2 FROM table_1 WHERE column_1 = 4 TIMES 4 SAVE TO ~/test.csv"
    simulate_ast = query.parseString(query_2,parseAll=True)
    assert simulate_ast.functions[0].column_id == 'col1'
    assert simulate_ast.functions[1].column_id == 'col2'

    query_3 = "SIMULATE col1, col2 FROM table_1"
    simulate_ast = query.parseString(query_3, parseAll=True)


def test_estimate_columns_from_pyparsing():
    query_1 = "ESTIMATE COLUMNS FROM table_1 WHERE col_1 = 4 ORDER BY TYPICALITY LIMIT 10 AS col_list_1"
    est_col_ast_1 = query.parseString(query_1,parseAll=True)
    assert est_col_ast_1.statement_id == 'estimate'
    assert est_col_ast_1.btable == 'table_1'
    assert est_col_ast_1.where_keyword == 'where'
    assert est_col_ast_1.where_conditions[0].function.column == 'col_1'
    assert est_col_ast_1.where_conditions[0].value == '4'
    assert est_col_ast_1.order_by[0].function.function_id == 'typicality'
    assert est_col_ast_1.limit == '10'
    assert est_col_ast_1.as_column_list == 'col_list_1'
    query_2 = "ESTIMATE COLUMNS FROM table_1"
    est_col_ast_2 = query.parseString(query_2,parseAll=True)
    assert est_col_ast_2.statement_id == 'estimate'
    assert est_col_ast_2.btable == 'table_1'

def test_estimate_pairwise_pyparsing():
    query_1 = "ESTIMATE PAIRWISE CORRELATION WITH col_1 FROM table_1"
    est_pairwise_ast_1 = query.parseString(query_1,parseAll=True)
    assert est_pairwise_ast_1.statement_id == 'estimate_pairwise'
    assert est_pairwise_ast_1.functions[0].function_id == 'correlation'
    assert est_pairwise_ast_1.functions[0].with_column == 'col_1'
    assert est_pairwise_ast_1.btable == 'table_1'
    query_2 = "ESTIMATE PAIRWISE DEPENDENCE PROBABILITY WITH col_1 FROM table_1 FOR col_1 SAVE TO file.csv SAVE CLUSTERS WITH THRESHOLD .4 AS col_list_1"
    est_pairwise_ast_2 = query.parseString(query_2,parseAll=True)
    assert est_pairwise_ast_2.statement_id == 'estimate_pairwise'
    assert est_pairwise_ast_2.functions[0].function_id == 'dependence probability'
    assert est_pairwise_ast_2.functions[0].with_column == 'col_1'
    assert est_pairwise_ast_2.btable == 'table_1'
    assert est_pairwise_ast_2.for_list.asList() == ['col_1']
    assert est_pairwise_ast_2.filename == 'file.csv'
    assert est_pairwise_ast_2.clusters_clause.threshold == '.4'
    assert est_pairwise_ast_2.clusters_clause.as_label == 'col_list_1'
    query_3 = "ESTIMATE PAIRWISE MUTUAL INFORMATION WITH col_1 FROM table_1"
    est_pairwise_ast_3 = query.parseString(query_3,parseAll=True)
    assert est_pairwise_ast_3.functions[0].function_id == 'mutual information'

def test_estimate_pairwise_row_pyparsing():
    query_1 = "ESTIMATE PAIRWISE ROW SIMILARITY FROM table_1 SAVE CLUSTERS WITH THRESHOLD .4 INTO table_2"
    est_pairwise_ast_1 = query.parseString(query_1,parseAll=True)
    assert est_pairwise_ast_1.statement_id == 'estimate_pairwise_row'
    assert est_pairwise_ast_1.functions[0].function_id == 'similarity'
    assert est_pairwise_ast_1.btable == 'table_1'
    query_2 = "ESTIMATE PAIRWISE ROW SIMILARITY FROM table_1 FOR a SAVE TO file.csv SAVE CLUSTERS WITH THRESHOLD .4 AS table_2"
    est_pairwise_ast_2 = query.parseString(query_2,parseAll=True)
    assert est_pairwise_ast_2.statement_id == 'estimate_pairwise_row'
    assert est_pairwise_ast_2.functions[0].function_id == 'similarity'
    assert est_pairwise_ast_2.btable == 'table_1'
    assert est_pairwise_ast_2.for_list.asList() == ['a']
    assert est_pairwise_ast_2.filename == 'file.csv'
    assert est_pairwise_ast_2.clusters_clause.threshold == '.4'
    assert est_pairwise_ast_2.clusters_clause.as_label == 'table_2'

def test_nested_queries_basic_pyparsing():
    query_1 = "SELECT * FROM ( SELECT col_1,col_2 FROM table_2)"
    ast = query.parseString(query_1,parseAll=True)
    assert ast.statement_id == 'select'
    assert ast.sub_query == " SELECT col_1,col_2 FROM table_2"
    ast_2 = query.parseString(ast.sub_query,parseAll=True)
    assert ast_2.statement_id == 'select'
    assert ast_2.functions[0].column_id == 'col_1'
    assert ast_2.functions[1].column_id == 'col_2'

def test_master_query_for_parse_errors():
    # This test will not test for correct information, just successfull parsing
    query_list = ["LIST BTABLES",
                  "SHOW SCHEMA FOR table_1",
                  "SHOW SCHEMA FOR table_1",
                  "SHOW DIAGNOSTICS FOR table_1",
                  "SHOW COLUMN LISTS FOR table_1",
                  "SHOW COLUMNS collist FOR table_1",
                  "LOAD MODELS ~/filename.csv INTO table_1",
                  "SAVE MODEL FROM table_1 to filename.pkl.gz",
                  "DROP BTABLE table_1",
                  "DROP MODEL 1 FROM table_1",
                  "DROP MODELS 1,2,6-9 FROM table_1",
                  "UPDATE SCHEMA FOR test_btablE SET col_1 = Categorical,col.2=numerical , col_3  =  ignore",
                  "CREATE BTABLE test.btable FROM '~/filenam e.csv'",
                  "CREATE BTABLE test_btable FROM ~/filename.csv",
                  "EXECUTE FILE '/filenam e.bql'",
                  "ANALYZE table_1 FOR 10 ITERATIONS",
                  "ANALYZE table_1 MODELS 1-3, 5-7, 9, 10 FOR 1 ITERATION",
                  "ANALYZE table_1 MODELS 1-3 FOR 1 ITERATION",
                  "SELECT TYPICALITY FROM table_1",
                  "SELECT TYPICALITY OF column_1 FROM table_1",
                  "SELECT PREDICTIVE PROBABILITY OF column_1 FROM table_1",
                  "SELECT PROBABILITY OF column_1 = 4 FROM table_1",
                  "SELECT SIMILARITY TO 0 FROM table_1",
                  "SELECT SIMILARITY TO column_1 = 4 FROM table_1",
                  "SELECT DEPENDENCE PROBABILITY WITH column_1 FROM table_1",
                  "SELECT MUTUAL INFORMATION OF column_1 WITH column_2 FROM table_1",
                  "SELECT CORRELATION OF column_1 WITH column_2 FROM table_1",
                  "SELECT TYPICALITY, PREDICTIVE PROBABILITY OF column_1 FROM table_1",
                  "SELECT SIMILARITY TO 0 WITH RESPECT TO column_1, col2 FROM table_1",
                  "SELECT SIMILARITY TO a = 1 , PROBABILITY OF a = 1 FROM table_1"]
#SELECT PREDICTIVE PROBABILITY OF a, MUTUAL INFORMATION OF a WITH b, CORRELATION OF a WITH b, DEPENDENCE PROBABILITY OF a WITH b, SIMILARITY TO 0, SIMILARITY TO a = 1, PROBABILITY OF a = 1 FROM table_1
    for query in query_list:
        query = bql_statement.parseString(query,parseAll=True)
        assert query.statement_id != ''

def test_list_btables():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('list btables',parseAll=True))
    assert method == 'list_btables'
    assert args == {}

def test_initialize_models():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('initialize 5 models for t',parseAll=True))
    assert method == 'initialize_models'
    assert args == dict(tablename='t', n_models=5, model_config=None)

def test_create_btable():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('create btable t from fn',parseAll=True))
    assert method == 'create_btable'
    assert args == dict(tablename='t', cctypes_full=None)
    assert client_dict == dict(csv_path=os.path.join(os.getcwd(), 'fn'))

def test_drop_btable():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('drop btable t',parseAll=True))
    assert method == 'drop_btable'
    assert args == dict(tablename='t')

def test_drop_models():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('drop models from t',parseAll=True))
    assert method == 'drop_models'
    assert args == dict(tablename='t', model_indices=None)

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('drop models 2-6 from t'))
    assert method == 'drop_models'
    assert args == dict(tablename='t', model_indices=range(2,7))

def test_analyze():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('analyze t models 2-6 for 3 iterations'))
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=3, seconds=None, ct_kernel=0, background=True)

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('analyze t for 6 iterations'))
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=None, iterations=6, seconds=None, ct_kernel=0, background=True)

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('analyze t for 7 minutes'))
    assert method == 'analyze'

    assert args == dict(tablename='t', model_indices=None, iterations=None, seconds=7*60, ct_kernel=0, background=True)

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('analyze t models 2-6 for 7 minutes'))
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=None, seconds=7*60, ct_kernel=0, background=True)

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('analyze t models 2-6 for 7 minutes with mh kernel'))
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=None, seconds=7*60, ct_kernel=1, background=True)

def test_load_models():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('load models fn into t'))
    assert method == 'load_models'
    assert args == dict(tablename='t')
    assert client_dict == dict(pkl_path='fn')

def test_save_models():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('save models from t to fn'))
    assert method == 'save_models'
    assert args == dict(tablename='t')
    assert client_dict == dict(pkl_path='fn')

def test_parse_functions():
    query_1 = "SELECT PREDICTIVE PROBABILITY OF a, MUTUAL INFORMATION OF a WITH b, CORRELATION OF a WITH b, DEPENDENCE PROBABILITY OF a WITH b, SIMILARITY TO 0, SIMILARITY TO a = 1 , PROBABILITY OF a = 1 , probability of b = 1 , TYPICALITY of a, typicality , a , * FROM table_1"
    ast_1 = bql_statement.parseString(query_1, parseAll=True)
    function_groups = ast_1.functions

    queries, query_cols = parser.parse_functions(function_groups, M_c = test_M_c, M_c_full = test_M_c_full, T=test_T, T_full = test_T_full)
    assert queries[0] == (functions._predictive_probability, 0, False)
    assert queries[1] == (functions._mutual_information, (0,1), True)
    assert queries[2] == (functions._correlation, (0,1), True)
    assert queries[3] == (functions._dependence_probability, (0,1), True)
    assert queries[4] == (functions._similarity, (0,None), False)
    assert queries[5] == (functions._similarity, (0,None), False)
    assert queries[6] == (functions._probability, (0,'1'), True)
    assert queries[7] == (functions._probability, (1,1), True)
    assert queries[8] == (functions._col_typicality, 0, True)
    assert queries[9] == (functions._row_typicality, True, False)
    assert queries[10] == (functions._column, (0, None), False)
    assert queries[11] == (functions._column, (0, None), False)
    assert queries[12] == (functions._column, (1, None), False)

def test_select():
    ##TODO test client_dict
    tablename = 't'
    newtablename = 'newtable'
    functions = function_in_query.parseString('*',parseAll=True)
    whereclause = None
    limit = float('inf')
    order_by = False
    plot = False

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('select * from t'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'] == d['whereclause']
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('summarize select * from t'))

    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=True)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'] == d['whereclause']
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('select a, b, a_b from t'))
    d = dict(tablename=tablename, functions=None, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == 'a'
    assert args['functions'][1].column_id == 'b'
    assert args['functions'][2].column_id == 'a_b'
    assert args['whereclause'] == d['whereclause']
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('select * from t where a=6 and b = 7'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == '*'
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    limit = 10
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('select * from t where a=6 and b = 7 limit 10'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('select * from t where a=6 and b = 7 order by b limit 10'))
    order_by = [('b', True)],
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    #assert args['order_by'] == d['order_by'] ##TODO
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('select * from t where a=6 and b = 7 order by b limit 10 into newtable'))
    order_by = [('b', True)],
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False, newtablename=newtablename)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    #assert args['order_by'] == d['order_by'] ##TODO
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']
    assert args['newtablename'] == d['newtablename']

    methods, args, client_dict = parser.parse_single_statement(bql_statement.parseString('freq select a from t'))
    d = dict(tablename=tablename, plot=plot, modelids=None, summarize=False, hist=False, freq=True)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']
    assert args['freq'] == d['freq']
    assert args['hist'] == d['hist']

    methods, args, client_dict = parser.parse_single_statement(bql_statement.parseString('hist select a from t'))
    d = dict(tablename=tablename, plot=plot, modelids=None, summarize=False, hist=True, freq=False)
    assert method == 'select'
    assert args['tablename'] == d['tablename']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['freq'] == d['freq']
    assert args['hist'] == d['hist']

def test_infer(): ##TODO
    ##TODO test client_dict
    tablename = 't'
    newtablename = 'newtable'
    functions = function_in_query.parseString('*',parseAll=True)
    whereclause = None
    limit = float('inf')
    order_by = False
    plot = False

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('infer * from t'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'infer'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'] == d['whereclause']
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('summarize infer * from t'))

    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=True)
    assert method == 'infer'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'] == d['whereclause']
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('infer a, b, a_b from t'))
    d = dict(tablename=tablename, functions=None, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'infer'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == 'a'
    assert args['functions'][1].column_id == 'b'
    assert args['functions'][2].column_id == 'a_b'
    assert args['whereclause'] == d['whereclause']
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('infer * from t where a=6 and b = 7'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'infer'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == '*'
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    limit = 10
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('infer * from t where a=6 and b = 7 limit 10'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'infer'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('infer * from t where a=6 and b = 7 limit 10 into newtable'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False, newtablename=newtablename)
    assert method == 'infer'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    assert args['order_by'] == d['order_by']
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']
    assert args['newtablename'] == d['newtablename']

    order_by = [('b', False)]
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('infer * from t where a=6 and b = 7 order by b limit 10'))
    d = dict(tablename=tablename, functions=functions, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'infer'
    assert args['tablename'] == d['tablename']
    assert args['functions'][0].column_id == d['functions'][0].column_id
    assert args['whereclause'][0].function.column == 'a'
    assert args['whereclause'][0].value == '6'
    assert args['whereclause'][1].function.column == 'b'
    assert args['whereclause'][1].value == '7'
    assert args['limit'] == d['limit']
    #assert args['order_by'] == d['order_by'] ##TODO
    assert args['plot'] == d['plot']
    assert args['modelids'] == d['modelids']
    assert args['summarize'] == d['summarize']

def test_simulate(): ##TODO
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('simulate * from t times 10'))
    assert method == 'simulate'
    assert args['tablename'] == 't'
    assert args['functions'][0].column_id == '*'
    assert args['summarize'] == False
    assert args['plot'] == False
    assert args['order_by'] == False
    assert args['modelids'] == None
    assert args['newtablename'] == None
    assert args['givens'] == None
    assert args['numpredictions'] == 10

    assert client_dict['pairwise'] == False
    assert client_dict['filename'] == None
    assert client_dict['scatter'] == False

    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('simulate * from t times 10 into newtable'))
    assert method == 'simulate'
    assert args['tablename'] == 't'
    assert args['functions'][0].column_id == '*'
    assert args['summarize'] == False
    assert args['plot'] == False
    assert args['order_by'] == False
    assert args['modelids'] == None
    assert args['newtablename'] == 'newtable'
    assert args['givens'] == None
    assert args['numpredictions'] == 10

    assert client_dict['pairwise'] == False
    assert client_dict['filename'] == None
    assert client_dict['scatter'] == False
    ##TODO more clauses

def test_estimate():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('estimate columns from t'))
    assert method == 'estimate_columns'
    assert args['tablename'] == 't'
    assert args['functions'][0] == 'column'
    assert args['whereclause'] == None
    assert args['limit'] == float('inf')
    assert args['order_by'] == False
    assert args['name'] == None
    assert args['modelids'] == None
    assert client_dict == None

def test_estimate_pairwise():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('estimate pairwise correlation from t'))
    assert method == 'estimate_pairwise'
    assert args['tablename'] == 't'
    assert args['function_name'] == 'correlation'
    assert args['column_list'] == None
    assert args['clusters_name'] == None
    assert args['threshold'] == None
    assert args['modelids'] == None
    assert client_dict['filename'] == None


def test_estimate_pairwise_row():
    method, args, client_dict = parser.parse_single_statement(bql_statement.parseString('estimate pairwise row similarity from t'))
    assert method == 'estimate_pairwise_row'
    assert args['tablename'] == 't'
    assert args['function'].function_id == 'similarity'
    assert args['row_list'] == None
    assert args['clusters_name'] == None
    assert args['threshold'] == None
    assert args['modelids'] == None
    assert client_dict['filename'] == None

def test_disallowed_queries():
    """
    All of these queries should pass the grammar and fail at parser.parse_query
    """
    strings = ["select * from test times 10",
               "select * from test save clusters with threshold .5 as test.csv",
               "select * from test given a=5",
               "select * from test with confidence .4",
               "select a conf .4 from test",
               "select a conf .4, b from test",
               "simulate a conf .4 from test times 10",
               "simulate a conf .4, b from test times 10",
               "infer * from test times 10",
               "infer typicality from test",
               "infer * from test with confidence 1.5",
               "simulate typicality from test",
               "infer * from test save clusters with threshold .5 as test.csv",
               "infer * from test given a=5",
               "simulate * from test where a < 4",
               "simulate * from test save clusters with threshold .5 as test.csv",
               "simulate * from test with confidence .4",
               "simulate * from test with 4 samples",
               "simulate * from test",
               "estimate columns from test with confidence .4",
               "estimate columns from test given a=4",
               "estimate columns from test times 10",
               "summarize estimate columns from test",
               "plot estimate columns from test",
               "estimate columns from test save clusters with threshold .5 as test.csv",
               "estimate pairwise correlation from test where a = b",
               "estimate pairwise correlation from test times 10",
               "estimate pairwise correlation from test given a = 5",
               "estimate pairwise correlation from test with confidence .2",
               "estimate pairwise row similarity from test where a = b",
               "estimate pairwise row similarity from test times 10",
               "estimate pairwise row similarity from test given a = 5",
               "estimate pairwise row similarity from test with confidence .2",
               "estimate pairwise row similarity from test where a = b"
               ]

    for query_string in strings:
        ast = bql_statement.parseString(query_string,parseAll=True)
        with pytest.raises(AssertionError):
            parser.parse_single_statement(ast)

def test_old_grammar_fails():
    """
    All of these queries are formerly valid but should not pass the current grammar.
    """

    strings = [
        'update schema for test set a = continuous',
        'update schema for test set a = multinomial',
        # Cyclic is invalid because it should be followed by (min, max) parameters.
        'update schema for test set a = cyclic'
    ]

    for query_string in strings:
        with pytest.raises(ParseException):
            ast = bql_statement.parseString(query_string, parseAll=True)

def test_label_and_metadata():
    # LABEL COLUMNS FOR <btable> SET <column1 = column-label-1> [, <column-name-2 = column-label-2>, ...]
    query_str1 = 'label columns for test set col_1 = label1, col_2 = "label 2"'
    ast = bql_statement.parseString(query_str1, parseAll=True)
    assert ast.label_clause[0][0] == 'col_1'
    assert ast.label_clause[0][1] == 'label1'
    assert ast.label_clause[1][0] == 'col_2'
    assert ast.label_clause[1][1] == 'label 2'

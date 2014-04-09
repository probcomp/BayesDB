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
from pyparsing import *

from bayesdb.bql_grammar import *
from bayesdb.engine import Engine
from bayesdb.parser import Parser
engine = Engine('local')
parser = Parser()

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
    second = second_keyword.parseString('second',parseAll=True)
    seconds = second_keyword.parseString('seconds',parseAll=True)
    assert second[0] == 'second'
    assert seconds[0] == 'second'

def test_composite_keywords_pyparsing():
    execute_file = execute_file_keyword.parseString('eXecute file',parseAll=True)
    assert execute_file[0] == 'execute file'
    create_btable = create_btable_keyword.parseString('cReate btable',parseAll=True)
    assert create_btable[0] == 'create btable'
    update_schema_for = update_schema_for_keyword.parseString('update Schema for',parseAll=True)
    assert update_schema_for[0] == 'update schema for'
    models_for = models_for_keyword.parseString('Models for',parseAll=True)
    assert models_for[0] == 'model for'
    model_index = model_index_keyword.parseString('model Index',parseAll=True)
    assert model_index[0] == 'model index'
    save_model = save_model_keyword.parseString("save modeL",parseAll=True)
    assert save_model[0] == 'save model'
    load_model = load_model_keyword.parseString("load Models",parseAll=True)
    assert load_model[0] == 'load model'
    save_to = save_to_keyword.parseString('save To',parseAll=True)
    assert save_to[0] == 'save to'
    list_btables = list_btables_keyword.parseString('list bTables',parseAll=True)
    assert list_btables[0] == 'list btable'
    show_schema_for = show_schema_for_keyword.parseString('show Schema for',parseAll=True)
    assert show_schema_for[0] == 'show schema for'
    show_models_for = show_models_for_keyword.parseString("show modeLs for",parseAll=True)
    assert show_models_for[0] == 'show model for'
    show_diagnostics_for = show_diagnostics_for_keyword.parseString("show diaGnostics for",parseAll=True)
    assert show_diagnostics_for[0] == 'show diagnostics for'
    estimate_pairwise = estimate_pairwise_keyword.parseString("estimate Pairwise",parseAll=True)
    assert estimate_pairwise[0] == 'estimate pairwise'
    with_confidence = with_confidence_keyword.parseString('with  confIdence',parseAll=True)
    assert with_confidence[0] == 'with confidence'
    dependence_probability = dependence_probability_keyword.parseString('dependence probability',parseAll=True)
    assert dependence_probability[0] == 'dependence probability'
    mutual_information = mutual_information_keyword.parseString('mutual inFormation',parseAll=True)
    assert mutual_information[0] == 'mutual information'
    estimate_columns_from = estimate_columns_from_keyword.parseString("estimate columns froM",parseAll=True)
    assert estimate_columns_from[0] == 'estimate column from'
    column_lists = column_lists_keyword.parseString('column Lists',parseAll=True)
    assert column_lists[0] == 'column list'
    similarity_to = similarity_to_keyword.parseString("similarity to",parseAll=True)
    assert similarity_to[0] == 'similarity to'
    with_respect_to = with_respect_to_keyword.parseString("with Respect to",parseAll=True)
    assert with_respect_to[0] == 'with respect to'
    probability_of = probability_of_keyword.parseString('probability of',parseAll=True)
    assert probability_of[0] == 'probability of'
    predictive_probability_of = predictive_probability_of_keyword.parseString('predictive Probability  of',parseAll=True)
    assert predictive_probability_of[0] == 'predictive probability of'
    save_connected_components_with_threshold = save_connected_components_with_threshold_keyword.parseString(
        'save cOnnected components with threshold',parseAll=True)
    assert save_connected_components_with_threshold[0] == 'save connected components with threshold'
    estimate_pairwise_row = estimate_pairwise_row_keyword.parseString("estimate Pairwise row",parseAll=True)
    assert estimate_pairwise_row[0] == 'estimate pairwise row'

def test_valid_values_names_pyparsing():
    valid_values=[
        '4',
        '42.04',
        '.4',
        '4.',
        "'\sjekja8391(*^@(%()!@#$%^&*()_+=-~'",
        "a0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~",
        'b0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~',
        '"c0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\\"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~"',
        "'d0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\\'()*+,-./:;<=>?@[\]^_`{|}~'",
        "'numbers 0'", 
        "'k skj s'",
        ]
    valid_values_results=[
        '4',
        '42.04',
        '.4',
        '4.',
        '\sjekja8391(*^@(%()!@#$%^&*()_+=-~',
        "a0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~",
        'b0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~',
        "c0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~",
        "d0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~",
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
    assert filename.parseString("!\"/#$%&'()*+,-.:;<=>?@[\]^_`{|}~",parseAll=True)[0] == "!\"/#$%&'()*+,-.:;<=>?@[\]^_`{|}~"
    assert filename.parseString("'/filename with space.csv'",parseAll=True)[0] == "/filename with space.csv"

def test_simple_functions():
    assert list_btables_function.parseString("LIST BTABLES",parseAll=True).statement_id == 'list btable'
    assert list_btables_function.parseString("LIST BTABLE",parseAll=True).statement_id == 'list btable'
    assert show_schema_for_function.parseString("SHOW SCHEMA FOR table_1",parseAll=True).statement_id == 'show schema for'
    assert show_schema_for_function.parseString("SHOW SCHEMA FOR table_1",parseAll=True).btable == 'table_1'
    assert show_models_for_function.parseString("SHOW MODELS FOR table_1",parseAll=True).statement_id == 'show model for'
    assert show_models_for_function.parseString("SHOW MODEL FOR table_1",parseAll=True).btable == 'table_1'
    assert show_diagnostics_for_function.parseString("SHOW DIAGNOSTICS FOR table_1",parseAll=True).statement_id == 'show diagnostics for'
    assert show_diagnostics_for_function.parseString("SHOW DIAGNOSTICS FOR table_1",parseAll=True).btable == 'table_1'
    assert load_model_function.parseString("LOAD MODELS ~/filename.csv INTO table_1",parseAll=True).statement_id == 'load model'
    assert load_model_function.parseString("LOAD MODEL ~/filename.csv INTO table_1",parseAll=True).statement_id == 'load model'
    assert load_model_function.parseString("LOAD MODELS ~/filename.csv INTO table_1",parseAll=True).filename == '~/filename.csv'
    assert load_model_function.parseString("LOAD MODELS '~/filena me.csv' INTO table_1",parseAll=True).filename == '~/filena me.csv'
    assert load_model_function.parseString("LOAD MODELS ~/filename.csv INTO table_1",parseAll=True).btable == 'table_1'
    assert save_model_from_function.parseString("SAVE MODEL FROM table_1 to filename.pkl.gz",parseAll=True).btable == 'table_1'
    assert save_model_from_function.parseString("SAVE MODEL FROM table_1 to filename.pkl.gz",parseAll=True).statement_id == 'save model'
    assert save_model_from_function.parseString("SAVE MODEL FROM table_1 to filename.pkl.gz",parseAll=True).filename == 'filename.pkl.gz'
    assert drop_btable_function.parseString("DROP BTABLE table_1",parseAll=True).statement_id == 'drop btable'
    assert drop_btable_function.parseString("DROP BTABLES table_1",parseAll=True).statement_id == 'drop btable'
    assert drop_btable_function.parseString("DROP BTABLE table_1",parseAll=True).btable == 'table_1'
    drop_model_1 = drop_model_function.parseString("DROP MODEL 1 FROM table_1",parseAll=True)
    drop_model_2 = drop_model_function.parseString("DROP MODELS 1-5 FROM table_1",parseAll=True)
    drop_model_3 = drop_model_function.parseString("DROP MODELS 1,2,6-9 FROM table_1",parseAll=True)
    drop_model_4 = drop_model_function.parseString("DROP MODELS 1-5,1-5 FROM table_1",parseAll=True)
    assert drop_model_1.statement_id == 'drop model'
    assert drop_model_1.btable == 'table_1'
    assert drop_model_1.index_list.asList() == [1]
    assert drop_model_2.index_list.asList() == [1,2,3,4,5]
    assert drop_model_3.index_list.asList() == [1,2,6,7,8,9]
    assert drop_model_4.index_list.asList() == [1,2,3,4,5]
    assert help_function.parseString("HELp",parseAll=True).statement_id == 'help'

def test_update_schema_pyparsing():
    update_schema_1 = update_schema_for_function.parseString("UPDATE SCHEMA FOR test_btablE SET col_1 = Categorical,col.2=numerical , col_3  =  ignore",parseAll=True)
    assert update_schema_1.statement_id == 'update schema for'
    assert update_schema_1.btable == 'test_btable'
    assert update_schema_1.type_clause[0][0] == 'col_1'
    assert update_schema_1.type_clause[0][1] == 'categorical'
    assert update_schema_1.type_clause[1][0] == 'col.2'
    assert update_schema_1.type_clause[1][1] == 'numerical'
    assert update_schema_1.type_clause[2][0] == 'col_3'
    assert update_schema_1.type_clause[2][1] == 'ignore'
    update_schema_2 = update_schema_for_function.parseString("UPDATE SCHEMA FOR test_btablE SET col_1 = key",parseAll=True)
    assert update_schema_2.type_clause[0][0] == 'col_1'
    assert update_schema_2.type_clause[0][1] == 'key'

def test_create_btable_pyparsing():
    create_btable_1 = create_btable_function.parseString("CREATE BTABLE test.btable FROM '~/filenam e.csv'", parseAll=True)
    create_btable_2 = create_btable_function.parseString("CREATE BTABLE test_btable FROM ~/filename.csv", parseAll=True)
    assert create_btable_1.statement_id == 'create btable'
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
    assert initialize_1.statement_id == 'initialize'
    assert initialize_1.num_models == '3'
    assert initialize_1.btable == 'test_table'
    initialize_2 = initialize_function.parseString("INITIALIZE 3 MODEL FOR test_table",parseAll=True)
    assert initialize_2.statement_id == 'initialize'
    assert initialize_2.num_models == '3'
    assert initialize_2.btable == 'test_table'

def test_analyze_pyparsing():
    analyze_1 = analyze_function.parseString("ANALYZE table_1 FOR 10 ITERATIONS",parseAll=True)
    analyze_2 = analyze_function.parseString("ANALYZE table_1 FOR 1 ITERATION",parseAll=True)
    analyze_3 = analyze_function.parseString("ANALYZE table_1 FOR 10 SECONDS",parseAll=True)
    analyze_4 = analyze_function.parseString("ANALYZE table_1 FOR 1 SECOND",parseAll=True)
    analyze_5 = analyze_function.parseString("ANALYZE table_1 MODEL 1 FOR 10 SECONDS",parseAll=True)
    analyze_6 = analyze_function.parseString("ANALYZE table_1 MODELS 1-3 FOR 1 ITERATION",parseAll=True)
    analyze_7 = analyze_function.parseString("ANALYZE table_1 MODELS 1,2,3 FOR 10 SECONDS",parseAll=True)
    analyze_8 = analyze_function.parseString("ANALYZE table_1 MODELS 1, 3-5 FOR 1 ITERATION",parseAll=True)
    analyze_9 = analyze_function.parseString("ANALYZE table_1 MODELS 1-3, 5 FOR 10 SECONDS",parseAll=True)
    analyze_10 = analyze_function.parseString("ANALYZE table_1 MODELS 1-3, 5-7, 9, 10 FOR 1 ITERATION",parseAll=True)
    analyze_11 = analyze_function.parseString("ANALYZE table_1 MODELS 1, 1, 2, 2 FOR 10 SECONDS",parseAll=True)
    analyze_12 = analyze_function.parseString("ANALYZE table_1 MODELS 1-5, 1-5, 5 FOR 1 ITERATION",parseAll=True)
    assert analyze_1.statement_id == 'analyze'
    assert analyze_1.btable == 'table_1'
    assert analyze_1.index_lust == ''
    assert analyze_1.index_clause == ''
    assert analyze_1.num_iterations == '10'
    assert analyze_1.num_seconds == ''
    assert analyze_2.num_iterations == '1'
    assert analyze_2.num_seconds == ''
    assert analyze_3.num_iterations == ''
    assert analyze_3.num_seconds == '10'
    assert analyze_4.num_iterations == ''
    assert analyze_4.num_seconds == '1'
    assert analyze_5.index_list.asList() == [1]
    assert analyze_6.index_list.asList() == [1,2,3]
    assert analyze_7.index_list.asList() == [1,2,3]
    assert analyze_8.index_list.asList() == [1,3,4,5]
    assert analyze_9.index_list.asList() == [1,2,3,5]
    assert analyze_10.index_list.asList() == [1,2,3,5,6,7,9,10]
    assert analyze_11.index_list.asList() == [1,2]
    assert analyze_12.index_list.asList() == [1,2,3,4,5]

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
    assert similarity_1.function.function_id == 'similarity to'
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

def test_probability_of_function_pyparsing():
    probability_of_1 = probability_of_function.parseString("PROBABILITY OF col_1 = 1",parseAll=True)
    probability_of_2 = probability_of_function.parseString("PROBABILITY OF col_1 = 'value'",parseAll=True)
    probability_of_3 = probability_of_function.parseString("PROBABILITY OF col_1 = value",parseAll=True)
    assert probability_of_1.function.function_id == 'probability of'
    assert probability_of_1.function.column == 'col_1'
    assert probability_of_1.function.value == '1'
    assert probability_of_2.function.value == 'value'
    assert probability_of_3.function.value == 'value'

def test_predictive_probability_of_pyparsing():
    assert predictive_probability_of_function.parseString("PREDICTIVE PROBABILITY OF column_1",
                                                          parseAll=True).function.function_id == 'predictive probability of'
    assert predictive_probability_of_function.parseString("PREDICTIVE PROBABILITY OF column_1",
                                                          parseAll=True).function.column == 'column_1'

def test_order_by_clause_pyparsing():
    order_by_1 = order_by_clause.parseString("ORDER BY column_1"
                                             ,parseAll=True)
    order_by_2 = order_by_clause.parseString("ORDER BY column_1,column_2 , column_3"
                                             ,parseAll=True)
    assert order_by_1.order_by.order_by_set[0].column=='column_1'
    assert order_by_2.order_by.order_by_set[1].column=='column_2'
    order_by_3 = order_by_clause.parseString("ORDER BY TYPICALITY",
                                             parseAll=True)
    assert order_by_3.order_by.order_by_set[0].function_id == 'typicality'
    order_by_4 = order_by_clause.parseString("ORDER BY TYPICALITY, column_1",
                                             parseAll=True)
    assert order_by_4.order_by.order_by_set[0].function_id == 'typicality'
    assert order_by_4.order_by.order_by_set[1].column == 'column_1'    
    order_by_5 = order_by_clause.parseString("ORDER BY column_1, TYPICALITY",
                                             parseAll=True)
    assert order_by_5.order_by.order_by_set[0].column == 'column_1'
    assert order_by_5.order_by.order_by_set[1].function_id == 'typicality'
    order_by_6 = order_by_clause.parseString("ORDER BY PREDICTIVE PROBABILITY OF column_1",
                                             parseAll=True)
    assert order_by_6.order_by.order_by_set[0].function_id == 'predictive probability of'
    assert order_by_6.order_by.order_by_set[0].column == 'column_1'
    
    order_by_7 = order_by_clause.parseString("ORDER BY PREDICTIVE PROBABILITY OF column_1, column_1",
                                             parseAll=True)
    assert order_by_7.order_by.order_by_set[1].column == 'column_1'
    assert order_by_7.order_by.order_by_set[0].function_id == 'predictive probability of'
    assert order_by_7.order_by.order_by_set[0].column == 'column_1'

    order_by_8 = order_by_clause.parseString("ORDER BY column_1, TYPICALITY, PREDICTIVE PROBABILITY OF column_1, column_2, SIMILARITY TO 2, SIMILARITY TO column_1 = 1 WITH RESPECT TO column_4",
                                             parseAll=True)
    assert order_by_8.order_by.order_by_set[0].column == 'column_1'
    assert order_by_8.order_by.order_by_set[1].function_id == 'typicality'
    assert order_by_8.order_by.order_by_set[2].function_id == 'predictive probability of'
    assert order_by_8.order_by.order_by_set[2].column == 'column_1'
    assert order_by_8.order_by.order_by_set[3].column == 'column_2'
    assert order_by_8.order_by.order_by_set[4].function_id == 'similarity to'
    assert order_by_8.order_by.order_by_set[4].row_id == '2'
    assert order_by_8.order_by.order_by_set[5].function_id == 'similarity to'
    assert order_by_8.order_by.order_by_set[5].column == 'column_1'
    assert order_by_8.order_by.order_by_set[5].column_value == '1'
    assert order_by_8.order_by.order_by_set[5].with_respect_to[1][0] == 'column_4' #todo names instead of indexes

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
    assert parsed_8.where_conditions[0].function.function_id == 'predictive probability of'
    assert parsed_8.where_conditions[0].function.column == 'column_1'
    assert parsed_8.where_conditions[0].operation == '>'
    assert parsed_8.where_conditions[0].value == '.1'
    whereclause_9 = "WHERE SIMILARITY TO 2 > .1"
    parsed_9 = where_clause.parseString(whereclause_9,parseAll=True)
    assert parsed_9.where_conditions[0].function.function_id == 'similarity to'
    assert parsed_9.where_conditions[0].function.row_id == '2'
    assert parsed_9.where_conditions[0].operation == '>'
    assert parsed_9.where_conditions[0].value == '.1'
    whereclause_10 = "WHERE SIMILARITY TO 2 WITH RESPECT TO column_1 > .4"
    parsed_10 = where_clause.parseString(whereclause_10,parseAll=True)
    assert parsed_10.where_conditions[0].function.function_id == 'similarity to'
    assert parsed_10.where_conditions[0].function.row_id == '2'
    assert parsed_10.where_conditions[0].function.with_respect_to.column_list[0] == 'column_1'
    assert parsed_10.where_conditions[0].operation == '>'
    assert parsed_10.where_conditions[0].value == '.4'
    whereclause_11 = "WHERE SIMILARITY TO column_1 = 1 = .5"
    parsed_11 = where_clause.parseString(whereclause_11,parseAll=True)
    assert parsed_11.where_conditions[0].function.function_id == 'similarity to'
    assert parsed_11.where_conditions[0].function.column == 'column_1'
    assert parsed_11.where_conditions[0].function.column_value == '1'
    assert parsed_11.where_conditions[0].operation == '='
    assert parsed_11.where_conditions[0].value == '.5'
    whereclause_12 = "WHERE SIMILARITY TO column_1 = 'a' WITH RESPECT TO column_2 > .5"
    parsed_12 = where_clause.parseString(whereclause_12,parseAll=True)
    assert parsed_12.where_conditions[0].function.function_id == 'similarity to'
    assert parsed_12.where_conditions[0].function.column == 'column_1'
    assert parsed_12.where_conditions[0].function.column_value == 'a'
    assert parsed_12.where_conditions[0].operation == '>'
    assert parsed_12.where_conditions[0].value == '.5'    
    assert parsed_12.where_conditions[0].function.with_respect_to.column_list[0] == 'column_2'
    whereclause_13 = "WHERE SIMILARITY TO column_1 = 1.2 WITH RESPECT TO column_2 > .5"
    parsed_13 = where_clause.parseString(whereclause_13,parseAll=True)
    assert parsed_13.where_conditions[0].function.function_id == 'similarity to'
    assert parsed_13.where_conditions[0].function.column == 'column_1'
    assert parsed_13.where_conditions[0].function.column_value == '1.2'
    assert parsed_13.where_conditions[0].operation == '>'
    assert parsed_13.where_conditions[0].value == '.5'    
    assert parsed_13.where_conditions[0].function.with_respect_to.column_list[0] == 'column_2'
    whereclause_14 = "WHERE SIMILARITY TO column_1 = a WITH RESPECT TO column_2 > .5"
    parsed_14 = where_clause.parseString(whereclause_14,parseAll=True)
    assert parsed_14.where_conditions[0].function.function_id == 'similarity to'
    assert parsed_14.where_conditions[0].function.column == 'column_1'
    assert parsed_14.where_conditions[0].function.column_value == 'a'
    assert parsed_14.where_conditions[0].operation == '>'
    assert parsed_14.where_conditions[0].value == '.5'    
    assert parsed_14.where_conditions[0].function.with_respect_to.column_list[0] == 'column_2'
    # With Confidence
    whereclause_15 = "WHERE TYPICALITY > .8 WITH CONFIDENCE .5"
    parsed_15 = where_clause.parseString(whereclause_15,parseAll=True)
    assert parsed_15.where_conditions[0].confidence == '.5'
    whereclause_16 = "WHERE PREDICTIVE PROBABILITY OF column_1 > .1 WITH CONFIDENCE .5"
    parsed_16 = where_clause.parseString(whereclause_16,parseAll=True)
    assert parsed_16.where_conditions[0].confidence == '.5'
    whereclause_17 = "WHERE SIMILARITY TO 2 > .1 WITH CONFIDENCE .5"
    parsed_17 = where_clause.parseString(whereclause_17,parseAll=True)
    assert parsed_17.where_conditions[0].confidence == '.5'
    whereclause_18 = "WHERE SIMILARITY TO 2 WITH RESPECT TO column_1 > .4 WITH CONFIDENCE .5"
    parsed_18 = where_clause.parseString(whereclause_18,parseAll=True)
    assert parsed_18.where_conditions[0].confidence == '.5'
    whereclause_19 = "WHERE SIMILARITY TO column_1 = 1 = .5 WITH CONFIDENCE .5"
    parsed_19 = where_clause.parseString(whereclause_19,parseAll=True)
    assert parsed_19.where_conditions[0].confidence == '.5'
    whereclause_20 = "WHERE SIMILARITY TO column_1 = 'a' WITH RESPECT TO column_2 > .5 WITH CONFIDENCE .5"
    parsed_20 = where_clause.parseString(whereclause_20,parseAll=True)
    assert parsed_20.where_conditions[0].confidence == '.5'
    whereclause_21 = "WHERE SIMILARITY TO column_1 = 1.2 WITH RESPECT TO column_2 > .5 WITH CONFIDENCE .5"
    parsed_21 = where_clause.parseString(whereclause_21,parseAll=True)
    assert parsed_21.where_conditions[0].confidence == '.5'
    whereclause_22 = "WHERE SIMILARITY TO column_1 = a WITH RESPECT TO column_2 > .5 WITH CONFIDENCE .5"
    parsed_22 = where_clause.parseString(whereclause_22,parseAll=True)
    assert parsed_22.where_conditions[0].confidence == '.5'
    # AND
    whereclause_23 = "WHERE column_1 = 'a' AND column_2 >= 3"
    parsed_23 = where_clause.parseString(whereclause_23,parseAll=True)
    assert parsed_23.where_conditions[0].function.column == 'column_1'
    assert parsed_23.where_conditions[1].function.column == 'column_2'
    whereclause_24 = "WHERE TYPICALITY > .8 AND PREDICTIVE PROBABILITY OF column_1 > .1 AND SIMILARITY TO 2 > .1"
    parsed_24 = where_clause.parseString(whereclause_24,parseAll=True)
    assert parsed_24.where_conditions[0].function.function_id == 'typicality'
    assert parsed_24.where_conditions[1].function.function_id == 'predictive probability of'
    assert parsed_24.where_conditions[2].function.function_id == 'similarity to'
    whereclause_25 = "WHERE TYPICALITY > .8 WITH CONFIDENCE .4 AND PREDICTIVE PROBABILITY OF column_1 > .1 WITH CONFIDENCE .6 AND SIMILARITY TO 2 > .1 WITH CONFIDENCE .5"
    parsed_25 = where_clause.parseString(whereclause_25,parseAll=True)
    assert parsed_25.where_conditions[0].confidence == '.4'
    assert parsed_25.where_conditions[1].confidence == '.6'
    assert parsed_25.where_conditions[2].confidence == '.5'
    whereclause_26 = "WHERE KEY IN row_list_1 AND column_1 = 'a' AND TYPICALITY > .4"
    parsed_26 = where_clause.parseString(whereclause_26,parseAll=True)
    assert parsed_26.where_conditions[0].function.function_id == 'key in'
    assert parsed_26.where_conditions[0].function.row_list == 'row_list_1'
    assert parsed_26.where_conditions[1].function.column == 'column_1'
    assert parsed_26.where_conditions[2].function.function_id == 'typicality'

def test_key_in_rowlist():
    assert key_in_rowlist_clause.parseString("key in row_list_1",parseAll=True).function.function_id == "key in"
    assert key_in_rowlist_clause.parseString("key in row_list_1",parseAll=True).function.row_list == "row_list_1"

def test_list_btables():
    method, args, client_dict = parser.parse_statement('list btables')
    assert method == 'list_btables'
    assert args == {}

def test_initialize_models():
    method, args, client_dict = parser.parse_statement('initialize 5 models for t')
    assert method == 'initialize_models'
    assert args == dict(tablename='t', n_models=5, model_config=None)

def test_create_btable():
    method, args, client_dict = parser.parse_statement('create btable t from fn')
    assert method == 'create_btable'
    assert args == dict(tablename='t', cctypes_full=None)
    assert client_dict == dict(csv_path=os.path.join(os.getcwd(), 'fn'))

def test_drop_btable():
    method, args, client_dict = parser.parse_statement('drop btable t')
    assert method == 'drop_btable'
    assert args == dict(tablename='t')

def test_drop_models():
    method, args, client_dict = parser.parse_statement('drop models for t')
    assert method == 'drop_models'
    assert args == dict(tablename='t', model_indices=None)

    method, args, client_dict = parser.parse_statement('drop models 2-6 for t')
    assert method == 'drop_models'
    assert args == dict(tablename='t', model_indices=range(2,7))

def test_analyze():
    method, args, client_dict = parser.parse_statement('analyze t models 2-6 for 3 iterations')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=3, seconds=None, ct_kernel=0)

    method, args, client_dict = parser.parse_statement('analyze t for 6 iterations')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=None, iterations=6, seconds=None, ct_kernel=0)

    method, args, client_dict = parser.parse_statement('analyze t for 7 seconds')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=None, iterations=None, seconds=7, ct_kernel=0)
    
    method, args, client_dict = parser.parse_statement('analyze t models 2-6 for 7 seconds')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=None, seconds=7, ct_kernel=0)

    method, args, client_dict = parser.parse_statement('analyze t models 2-6 for 7 seconds with mh kernel')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=None, seconds=7, ct_kernel=1)    

def test_load_models():
    method, args, client_dict = parser.parse_statement('load models fn for t')
    assert method == 'load_models'
    assert args == dict(tablename='t')
    assert client_dict == dict(pkl_path='fn')

def test_save_models():
    method, args, client_dict = parser.parse_statement('save models for t to fn')
    assert method == 'save_models'
    assert args == dict(tablename='t')
    assert client_dict == dict(pkl_path='fn')

def test_select():
    tablename = 't'
    columnstring = '*'
    whereclause = ''
    limit = float('inf')
    order_by = False
    plot = False

    method, args, client_dict = parser.parse_statement('select * from t')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args == d

    method, args, client_dict = parser.parse_statement('summarize select * from t')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=True)
    assert method == 'select'
    assert args == d
    
    columnstring = 'a, b, a_b'
    method, args, client_dict = parser.parse_statement('select a, b, a_b from t')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args == d

    whereclause = 'a=6 and b = 7'
    columnstring = '*'
    method, args, client_dict = parser.parse_statement('select * from t where a=6 and b = 7')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args == d

    limit = 10
    method, args, client_dict = parser.parse_statement('select * from t where a=6 and b = 7 limit 10')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args == d

    order_by = [('b', False)]
    method, args, client_dict = parser.parse_statement('select * from t where a=6 and b = 7 order by b limit 10')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot, modelids=None, summarize=False)
    assert method == 'select'
    assert args == d

def test_simulate():
    tablename = 't'
    newtablename = ''
    columnstring = ''
    whereclause = ''
    order_by = ''
    numpredictions = ''
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             newtablename=newtablename, order_by=order_by, numpredictions=numpredictions)
    

def test_infer():
    tablename = 't'
    newtablename = ''
    columnstring = ''
    confidence = ''
    whereclause = ''
    limit = ''
    numsamples = ''
    order_by = ''
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             newtablename=newtablename, order_by=order_by, numsamples=numsamples, confidence=confidence)


#SELECT <columns> FROM <btable> [WHERE <whereclause>] [LIMIT <limit>] [ORDER BY <columns>]

#INFER <columns> FROM <btable> [WHERE <whereclause>] [WITH CONFIDENCE <confidence>] [LIMIT <limit>] [WITH <numsamples> SAMPLES] [ORDER BY <columns]

#SIMULATE <columns> FROM <btable> [WHERE <whereclause>] TIMES <times> [ORDER BY <columns>]

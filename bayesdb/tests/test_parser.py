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
    model = model_keyword.parseString("model")
    models = model_keyword.parseString("models")
    assert model[0] == 'model'
    assert models[0] == 'model'
    iteration = iteration_keyword.parseString("iteration")
    iterations = iteration_keyword.parseString("iterations")
    assert iteration[0] == 'iteration'
    assert iterations[0] == 'iteration'
    sample = sample_keyword.parseString("sample")
    samples = sample_keyword.parseString("samples")
    assert sample[0] == 'sample'
    assert samples[0] == 'sample'
    column = column_keyword.parseString('column')
    columns = column_keyword.parseString('columns')
    assert column[0] == 'column'
    assert columns[0] == 'column'
    list_ = list_keyword.parseString('list')
    lists = list_keyword.parseString('lists')
    assert list_[0] == 'list'
    assert lists[0] == 'list'
    btable = btable_keyword.parseString('btable')
    btables = btable_keyword.parseString('btables')
    assert btable[0] == 'btable'
    assert btables[0] == 'btable'
    second = second_keyword.parseString('second')
    seconds = second_keyword.parseString('seconds')
    assert second[0] == 'second'
    assert seconds[0] == 'second'

def test_composite_keywords_pyparsing():
    execute_file = execute_file_keyword.parseString('eXecute file')
    assert execute_file[0] == 'execute file'
    create_btable = create_btable_keyword.parseString('cReate btable')
    assert create_btable[0] == 'create btable'
    update_schema_for = update_schema_for_keyword.parseString('update Schema for')
    assert update_schema_for[0] == 'update schema for'
    models_for = models_for_keyword.parseString('Models for')
    assert models_for[0] == 'model for'
    model_index = model_index_keyword.parseString('model Index')
    assert model_index[0] == 'model index'
    save_model = save_model_keyword.parseString("save modeL")
    assert save_model[0] == 'save model'
    load_model = load_model_keyword.parseString("load Models")
    assert load_model[0] == 'load model'
    save_to = save_to_keyword.parseString('save To')
    assert save_to[0] == 'save to'
    list_btables = list_btables_keyword.parseString('list bTables')
    assert list_btables[0] == 'list btable'
    show_schema_for = show_schema_for_keyword.parseString('show Schema for')
    assert show_schema_for[0] == 'show schema for'
    show_models_for = show_models_for_keyword.parseString("show modeLs for")
    assert show_models_for[0] == 'show model for'
    show_diagnostics_for = show_diagnostics_for_keyword.parseString("show diaGnostics for")
    assert show_diagnostics_for[0] == 'show diagnostics for'
    estimate_pairwise = estimate_pairwise_keyword.parseString("estimate Pairwise")
    assert estimate_pairwise[0] == 'estimate pairwise'
    with_confidence = with_confidence_keyword.parseString('with  confIdence')
    assert with_confidence[0] == 'with confidence'
    dependence_probability = dependence_probability_keyword.parseString('dependence probability')
    assert dependence_probability[0] == 'dependence probability'
    mutual_information = mutual_information_keyword.parseString('mutual inFormation')
    assert mutual_information[0] == 'mutual information'
    estimate_columns_from = estimate_columns_from_keyword.parseString("estimate columns froM")
    assert estimate_columns_from[0] == 'estimate column from'
    column_lists = column_lists_keyword.parseString('column Lists')
    assert column_lists[0] == 'column list'
    similarity_to = similarity_to_keyword.parseString("similarity to")
    assert similarity_to[0] == 'similarity to'
    with_respect_to = with_respect_to_keyword.parseString("with Respect to")
    assert with_respect_to[0] == 'with respect to'
    probability_of = probability_of_keyword.parseString('probability of')
    assert probability_of[0] == 'probability of'
    predictive_probability_of = predictive_probability_of_keyword.parseString('predictive Probability  of')
    assert predictive_probability_of[0] == 'predictive probability of'
    save_connected_components_with_threshold = save_connected_components_with_threshold_keyword.parseString(
        'save cOnnected components with threshold')
    assert save_connected_components_with_threshold[0] == 'save connected components with threshold'
    estimate_pairwise_row = estimate_pairwise_row_keyword.parseString("estimate Pairwise row")
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
        assert value.parseString(valid_values[i])[0] == valid_values_results[i]

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
        assert value.parseString(valid_column_identifiers[i])[0] == valid_column_identifiers_results[i]
    assert float_number.parseString('1')[0] == '1'
    assert int_number.parseString('1')[0] == '1'
    assert float_number.parseString('1.')[0] == '1'
    assert float_number.parseString('.1')[0] == '.1'
    assert float_number.parseString('0.1')[0] == '0.1'
    assert float_number.parseString('11')[0] == '11'
    assert int_number.parseString('11')[0] == '11'
    assert float_number.parseString('11.01')[0] == '11.01'
    assert filename.parseString("~/filename.csv")[0] == "~/filename.csv"
    assert filename.parseString("!\"/#$%&'()*+,-.:;<=>?@[\]^_`{|}~")[0] == "!\"/#$%&'()*+,-.:;<=>?@[\]^_`{|}~"
    assert filename.parseString("'/filename with space.csv'")[0] == "/filename with space.csv"

def test_update_schema_pyparsing():
    update_schema_1 = update_schema_for_function.parseString("UPDATE SCHEMA FOR test_btablE SET col_1 = Categorical,col.2=numerical , col_3  =  ignore",parseAll=True)
    assert update_schema_1.function_id == 'update schema for'
    assert update_schema_1.btable == 'test_btablE'
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
    assert create_btable_1.function_id == 'create btable'
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
    assert initialize_1.function_id == 'initialize'
    assert initialize_1.num_models == '3'
    assert initialize_1.btable == 'test_table'

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
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=3, seconds=None)

    method, args, client_dict = parser.parse_statement('analyze t for 6 iterations')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=None, iterations=6, seconds=None)

    method, args, client_dict = parser.parse_statement('analyze t for 7 seconds')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=None, iterations=None, seconds=7)
    
    method, args, client_dict = parser.parse_statement('analyze t models 2-6 for 7 seconds')
    assert method == 'analyze'
    assert args == dict(tablename='t', model_indices=range(2,7), iterations=None, seconds=7)

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
             limit=limit, order_by=order_by, plot=plot)
    assert method == 'select'
    assert args == d

    columnstring = 'a, b, a_b'
    method, args, client_dict = parser.parse_statement('select a, b, a_b from t')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot)
    assert method == 'select'
    assert args == d

    whereclause = 'a=6 and b = 7'
    columnstring = '*'
    method, args, client_dict = parser.parse_statement('select * from t where a=6 and b = 7')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot)
    assert method == 'select'
    assert args == d

    limit = 10
    method, args, client_dict = parser.parse_statement('select * from t where a=6 and b = 7 limit 10')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot)
    assert method == 'select'
    assert args == d

    order_by = [('b', False)]
    method, args, client_dict = parser.parse_statement('select * from t where a=6 and b = 7 order by b limit 10')
    d = dict(tablename=tablename, columnstring=columnstring, whereclause=whereclause,
             limit=limit, order_by=order_by, plot=plot)
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

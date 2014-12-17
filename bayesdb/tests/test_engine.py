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
import numpy
import pytest
import random

import bayesdb.diagnostics_utils as diag_utils
import bayesdb.data_utils as data_utils
from bayesdb.client import Client
from bayesdb.engine import Engine
from bayesdb.parser import Parser
import bayesdb.bql_grammar as bql
import bayesdb.utils as utils

engine = Engine()
parser = Parser()

test_tablenames = None


notimplemented = pytest.mark.skipif(True, reason="Test not implemented")


def setup_function(function):
    global test_tablenames
    test_tablenames = []
    global engine
    engine = Engine()


def teardown_function(function):
    global tablename
    for test_tablename in test_tablenames:
        engine.drop_btable(test_tablename)


def create_dha(path='data/dha.csv'):
    test_tablename = 'dhatest' + str(int(time.time() * 1000000)) + \
        str(int(random.random()*10000000))
    header, rows = data_utils.read_csv(path)
    create_btable_result = engine.create_btable(test_tablename, header, rows, key_column=0)
    # metadata = engine.persistence_layer.get_metadata(test_tablename)

    global test_tablenames
    test_tablenames.append(test_tablename)

    return test_tablename, create_btable_result


def create_describe_btable(data_path='data/describe.csv',
                           codebook_path='data/describe_codebook.csv', use_codebook=True):
    # TODO: refactor codebook generation to Engine, not Client
    test_tablename = 'describetest' + str(int(time.time() * 1000000)) + \
        str(int(random.random()*10000000))

    if use_codebook:
        codebook_header, codebook_rows = data_utils.read_csv(codebook_path)
        codebook = dict()
        for codebook_row in codebook_rows:
            codebook[codebook_row[0]] = dict(zip(['short_name', 'description', 'value_map'],
                                             codebook_row[1:]))
    else:
        codebook = None

    header, rows = data_utils.read_csv(data_path)
    create_btable_result = engine.create_btable(test_tablename, header, rows, key_column=0,
                                                codebook=codebook)

    global test_tablenames
    test_tablenames.append(test_tablename)

    return test_tablename, create_btable_result


def test_create_btable():
    test_tablename, create_btable_result = create_dha()
    assert 'column_labels' in create_btable_result
    assert 'data' in create_btable_result
    assert 'message' in create_btable_result
    # Should be 65 rows (1 for each column inferred: 64 from data file, plus 1 for key)
    assert len(create_btable_result['data']) == 65
    # Should be 3 columns: 1 for column names, 1 for data type, and 1 for parameters
    assert len(create_btable_result['data'][0]) == 3
    list_btables_result = engine.list_btables()['data']
    assert [test_tablename] in list_btables_result
    engine.drop_btable(test_tablename)


def test_drop_btable():
    test_tablename, _ = create_dha()
    list_btables_result = engine.list_btables()['data']
    assert [test_tablename] in list_btables_result
    engine.drop_btable(test_tablename)
    list_btables_result = engine.list_btables()['data']
    assert [test_tablename] not in list_btables_result


def test_select():
    test_tablename, _ = create_dha()

    # Test a simple query: select two columns, no limit, no order, no where.
    # Check to make sure types of all inputs are correct, etc.

    functions = bql.bql_statement.parseString('select name, qual_score from test',
                                              parseAll=True).functions
    whereclause = None
    limit = float('inf')
    order_by = False
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)
    assert 'column_labels' in select_result
    assert 'data' in select_result
    assert select_result['column_labels'] == ['key', 'name', 'qual_score']
    # 307 is the total number of rows in the dataset.
    assert(len(select_result['data']) == 307 and
           len(select_result['data'][0]) == len(select_result['column_labels']))
    assert type(select_result['data'][0][0]) == numpy.string_
    t = type(select_result['data'][0][1])
    assert (t == unicode) or (t == str) or (t == numpy.string_)  # type of name is unicode or string
    assert type(select_result['data'][0][2]) == float  # type of qual_score is float
    original_select_result = select_result['data']

    # Test limit: do the same query as before, but limit to 10
    limit = 10
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)
    assert len(select_result['data']) == limit

    # Test order by single column: desc
    ground_truth_ordered_results = sorted(original_select_result, key=lambda t: t[2],
                                          reverse=True)[:10]
    order_by = [('qual_score', True)]
    order_by = bql.bql_statement.parseString('select name, qual_score, similarity to 5 from test '
                                             'order by qual_score desc', parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)
    assert select_result['data'] == ground_truth_ordered_results

    # Test order by single column: asc
    ground_truth_ordered_results = sorted(original_select_result, key=lambda t: t[2])[:10]
    order_by = [('qual_score', False)]
    order_by = bql.bql_statement.parseString('select name, qual_score, similarity to 5 from test '
                                             'order by qual_score asc', parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)
    assert select_result['data'] == ground_truth_ordered_results

    engine.initialize_models(test_tablename, 2)

    # SIMILARITY TO <row> [WITH RESPECT TO <col>]
    # smoke tests
    functions = bql.bql_statement.parseString('select name, qual_score, similarity to 5 from test '
                                              'order by similarity to 5', parseAll=True).functions
    order_by = bql.bql_statement.parseString('select name, qual_score, similarity to 5 from test '
                                             'order by similarity to 5', parseAll=True).order_by

    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    functions = bql.bql_statement.parseString('select name, qual_score, similarity to 5 from test '
                                              'order by similarity to 5', parseAll=True).functions
    order_by = bql.bql_statement.parseString('select name, qual_score, similarity to 5 from test '
                                             'order by similarity to 5 with respect to qual_score',
                                             parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    functions = bql.bql_statement.parseString('select name, qual_score from test',
                                              parseAll=True).functions
    order_by = bql.bql_statement.parseString('select * from test order by similarity to 5 with '
                                             'respect to qual_score', parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    functions = bql.bql_statement.parseString('select name, qual_score, similarity to 5 with '
                                              'respect to name from test', parseAll=True).functions
    order_by = bql.bql_statement.parseString('select * from test order by similarity to 5',
                                             parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    functions = bql.bql_statement.parseString("select name, qual_score, similarity to "
                                              "name='Albany NY' with respect to qual_score from "
                                              "test", parseAll=True).functions
    order_by = bql.bql_statement.parseString('select * from test order by similarity to 5',
                                             parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    functions = bql.bql_statement.parseString('select * from test', parseAll=True).functions
    order_by = bql.bql_statement.parseString('select * from test order by similarity to 5 with '
                                             'respect to name', parseAll=True).order_by
    whereclause = bql.bql_statement.parseString('select * from test where qual_score > 6',
                                                parseAll=True).where_conditions
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    # Albany NY's row id is 3
    whereclause = bql.bql_statement.parseString('select * from test where name="Albany NY"',
                                                parseAll=True).where_conditions
    functions = bql.bql_statement.parseString('select * from test', parseAll=True).functions
    order_by = bql.bql_statement.parseString('select * from test order by similarity to 5 with '
                                             'respect to name', parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    # TYPICALITY (of row)
    # smoke tests
    order_by = False
    whereclause = None
    functions = bql.bql_statement.parseString('select name, qual_score, typicality from test',
                                              parseAll=True).functions
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    functions = bql.bql_statement.parseString('select name, qual_score, typicality from test',
                                              parseAll=True).functions
    order_by = bql.bql_statement.parseString('select * from test order by typicality',
                                             parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    # TODO: test all other single-column functions
    # PROBABILITY <col>=<val>
    # PREDICTIVE PROBABILITY

    # TODO: test all single-column aggregate functions

    # TYPICALITY OF <col>
    functions = bql.bql_statement.parseString('select typicality of name from test',
                                              parseAll=True).functions
    order_by = bql.bql_statement.parseString('select * from test order by typicality',
                                             parseAll=True).order_by
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)

    # DEPENDENCE PROBABILITY OF <col> WITH <col> #DEPENDENCE PROBABILITY TO <col>
    # MUTUAL INFORMATION OF <col> WITH <col> #MUTUAL INFORMATION WITH <col>
    # CORRELATION OF <col> WITH <col>

    # TODO: test ordering by functions

@notimplemented
def test_delete_model():
    pass  # TODO


def test_update_schema():
    test_tablename, _ = create_dha()
    m_c, m_r, t = engine.persistence_layer.get_metadata_and_table(test_tablename)
    cctypes = engine.persistence_layer.get_cctypes(test_tablename)
    assert cctypes[m_c['name_to_idx']['qual_score']] == 'numerical'
    assert cctypes[m_c['name_to_idx']['name']] == 'categorical'

    # Categorical with no cardinality parameter
    mappings = dict(qual_score=dict(cctype='categorical', parameters=None))
    engine.update_schema(test_tablename, mappings)
    cctypes = engine.persistence_layer.get_cctypes(test_tablename)
    assert cctypes[m_c['name_to_idx']['qual_score']] == 'categorical'

    # Categorical with optional cardinality parameter
    mappings = dict(name=dict(cctype='categorical', parameters=dict(cardinality=350)))
    engine.update_schema(test_tablename, mappings)
    cctypes = engine.persistence_layer.get_cctypes(test_tablename)
    assert cctypes[m_c['name_to_idx']['name']] == 'categorical'

    # Cyclic with required min, max parameters
    mappings = dict(qual_score=dict(cctype='cyclic', parameters=dict(min=0, max=100)))
    engine.update_schema(test_tablename, mappings)
    cctypes = engine.persistence_layer.get_cctypes(test_tablename)
    assert cctypes[m_c['name_to_idx']['qual_score']] == 'cyclic'

    # Ignore
    mappings = dict(qual_score=dict(cctype='ignore', parameters=None))
    engine.update_schema(test_tablename, mappings)
    m_c, m_r, t = engine.persistence_layer.get_metadata_and_table(test_tablename)
    cctypes = engine.persistence_layer.get_cctypes(test_tablename)
    assert 'qual_score' not in m_c['name_to_idx'].keys()

    # Now test that it doesn't allow name to be continuous
    mappings = dict(name=dict(cctype='numerical', parameters=None))
    with pytest.raises(ValueError):
        engine.update_schema(test_tablename, mappings)

    # Test that setting cyclic with parameters inside the range of data fails
    mappings = dict(qual_score=dict(cctype='cyclic', parameters=dict(min=50, max=60)))
    with pytest.raises(utils.BayesDBError):
        engine.update_schema(test_tablename, mappings)

    # Test that setting categorical with low cardinality fails
    mappings = dict(name=dict(cctype='categorical', parameters=dict(cardinality=10)))
    with pytest.raises(utils.BayesDBError):
        engine.update_schema(test_tablename, mappings)


def test_save_and_load_models():
    test_tablename, _ = create_dha()
    engine.initialize_models(test_tablename, 3)
    engine.analyze(test_tablename, model_indices='all', iterations=1, background=False)
    # note that this won't save the models, since we didn't call this from the client.
    # engine.save_models actually just returns the models.
    original_models = engine.save_models(test_tablename)

    test_tablename2, _ = create_dha()
    models = original_models['models']
    model_schema = original_models['schema']
    engine.load_models(test_tablename2, models, model_schema)
    assert engine.save_models(test_tablename2).values() == original_models.values()


def test_initialize_models():
    test_tablename, _ = create_dha(path='data/dha_missing.csv')

    engine = Engine(seed=0)
    num_models = 5
    engine.initialize_models(test_tablename, num_models)

    model_ids = engine.persistence_layer.get_model_ids(test_tablename)
    assert sorted(model_ids) == range(num_models)
    for i in range(num_models):
        model = engine.persistence_layer.get_models(test_tablename, i)
        assert model['iterations'] == 0


def test_analyze():
    test_tablename, _ = create_dha()
    num_models = 3
    engine.initialize_models(test_tablename, num_models)

    for it in (1, 2):
        engine.analyze(test_tablename, model_indices='all', iterations=1, background=True)

        while 'not currently being analyzed' not in engine.show_analyze(test_tablename)['message']:
            import time
            time.sleep(0.1)

        # analyze_results = engine.show_analyze(test_tablename)
        model_ids = engine.persistence_layer.get_model_ids(test_tablename)
        assert sorted(model_ids) == range(num_models)
        for i in range(num_models):
            model = engine.persistence_layer.get_models(test_tablename, i)
            assert model['iterations'] == it

    for it in (3, 4):  # models were analyzed by previous for loop, so start counting at 3.
        engine.analyze(test_tablename, model_indices='all', iterations=1, background=False)
        analyze_results = engine.show_analyze(test_tablename)
        assert 'not currently being analyzed' in analyze_results['message']
        model_ids = engine.persistence_layer.get_model_ids(test_tablename)
        assert sorted(model_ids) == range(num_models)
        for i in range(num_models):
            model = engine.persistence_layer.get_models(test_tablename, i)
            assert model['iterations'] == it


def test_subsampling():
    # Use Kiva table, which has 10000 rows, instead of DHA.
    test_tablename = 'kivatest' + str(int(time.time() * 1000000)) + \
        str(int(random.random()*10000000))
    global test_tablenames
    test_tablenames.append(test_tablename)

    path = 'data/kiva_small.csv'
    header, rows = data_utils.read_csv(path)

    num_rows = 4  # rows in kiva_small
    num_rows_subsample = 2

    # client('create btable %s from %s' % (test_tablename, path), debug=True, pretty=False)
    # only analyze using some rows
    engine.create_btable(test_tablename, header, rows, subsample=num_rows_subsample, key_column=0)
    # make sure select (using no models) works and returns the correct number of rows
    functions = bql.bql_statement.parseString('select loan_id, loan_status from test',
                                              parseAll=True).functions
    whereclause = None
    limit = float('inf')
    order_by = False
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)
    assert len(select_result['data']) == num_rows  # number of rows in Kiva

    # TODO: better testing to see what we can do before subsampling (with partial models)

    num_models = 2
    iterations = 1
    engine.initialize_models(test_tablename, num_models)
    # analyze segfaults
    engine.analyze(test_tablename, model_indices='all', iterations=iterations, background=False)
    print('analyzed')
    model_ids = engine.persistence_layer.get_model_ids(test_tablename)
    for i in range(num_models):
        model = engine.persistence_layer.get_models(test_tablename, i)
        assert model['iterations'] == iterations

    # make sure normal queries work and return the correct number of rows
    functions = bql.bql_statement.parseString('select loan_id, predictive probability of '
                                              'loan_status from test', parseAll=True).functions
    whereclause = None
    limit = float('inf')
    order_by = False
    select_result = engine.select(test_tablename, functions, whereclause, limit, order_by, None)
    assert len(select_result['data']) == num_rows  # number of rows in Kiva


def test_nan_handling():
    test_tablename1, _ = create_dha(path='data/dha_missing.csv')
    test_tablename2, _ = create_dha(path='data/dha_missing_nan.csv')
    m1 = engine.persistence_layer.get_metadata(test_tablename1)
    m2 = engine.persistence_layer.get_metadata(test_tablename2)
    assert m1['M_c'] == m2['M_c']
    assert m1['M_r'] == m2['M_r']
    assert m1['cctypes'] == m2['cctypes']
    numpy.testing.assert_equal(numpy.array(m1['T']), numpy.array(m2['T']))


def test_infer():
    # TODO: whereclauses
    test_tablename, _ = create_dha(path='data/dha_missing.csv')

    # dha_missing has missing qual_score in first 5 rows, and missing name in rows 6-10.
    engine = Engine(seed=0)
    engine.initialize_models(test_tablename, 20)

    functions = bql.bql_statement.parseString('infer name, qual_score from test',
                                              parseAll=True).functions
    whereclause = None
    limit = float('inf')
    order_by = False
    numsamples = 30
    confidence = 0
    infer_result = engine.infer(test_tablename, functions, confidence, whereclause, limit,
                                numsamples, order_by)
    assert 'column_labels' in infer_result
    assert 'data' in infer_result
    assert infer_result['column_labels'] == ['key', 'name', 'qual_score']
    # 307 is the total number of rows in the dataset.
    assert(len(infer_result['data']) == 307 and
           len(infer_result['data'][0]) == len(infer_result['column_labels']))
    assert type(infer_result['data'][0][0]) == numpy.string_  # type of key is int
    t = type(infer_result['data'][0][1])
    assert (t == unicode) or (t == numpy.string_)  # type of name is string
    assert type(infer_result['data'][0][2]) == float  # type of qual_score is float

    all_possible_names = [infer_result['data'][row][1] for row in range(5) + range(10, 307)]
    all_observed_qual_scores = [infer_result['data'][row][2] for row in range(5, 307)]

    for row in range(5):
        inferred_name = infer_result['data'][row+5][1]
        inferred_qual_score = infer_result['data'][row][2]
        assert inferred_name in all_possible_names
        assert type(inferred_qual_score) == type(1.2)
        assert inferred_qual_score > min(all_observed_qual_scores)
        assert inferred_qual_score < max(all_observed_qual_scores)

    # Now, try infer with higher confidence, and make sure that name isn't inferred anymore.
    confidence = 0.9
    infer_result = engine.infer(test_tablename, functions, confidence, whereclause, limit,
                                numsamples, order_by)

    for row in range(5):
        # TODO: what do missing values look like? these should be missing
        inferred_name = infer_result['data'][row+5][1]
        inferred_qual_score = infer_result['data'][row][2]
        assert numpy.isnan(inferred_name)
        assert numpy.isnan(inferred_qual_score)


def test_simulate():
    # TODO: whereclauses
    test_tablename, _ = create_dha()
    engine.initialize_models(test_tablename, 2)

    columnstring = 'name, qual_score'
    functions = bql.bql_statement.parseString('simulate name, qual_score from test',
                                              parseAll=True).functions
    whereclause = None
    givens = None
    order_by = False
    numpredictions = 10
    simulate_result = engine.simulate(test_tablename, functions, givens, numpredictions, order_by)
    assert 'column_labels' in simulate_result
    assert 'data' in simulate_result
    assert simulate_result['column_labels'] == ['name', 'qual_score']

    assert(len(simulate_result['data']) == 10 and
           len(simulate_result['data'][0]) == len(simulate_result['column_labels']))
    for row in range(numpredictions):
        t = type(simulate_result['data'][row][0])
        assert (t == unicode) or (t == numpy.string_)
        assert type(simulate_result['data'][row][1]) == float


def test_estimate_pairwise_dependence_probability():
    test_tablename, _ = create_dha()
    engine.initialize_models(test_tablename, 2)
    dep_mat = engine.estimate_pairwise(test_tablename, 'dependence probability')


@pytest.mark.skipif(True, reason="Calculation too slow due to analysis on non-ignored, unique, "
                    "multinomial 'name' variable")
def test_estimate_pairwise_mutual_information():
    test_tablename, _ = create_dha()
    engine.initialize_models(test_tablename, 2)
    mi_mat = engine.estimate_pairwise(test_tablename, 'mutual information', numsamples=2)


def test_estimate_pairwise_correlation():
    test_tablename, _ = create_dha()
    engine.initialize_models(test_tablename, 2)
    cor_mat = engine.estimate_pairwise(test_tablename, 'correlation')


def test_list_btables():
    list_btables_result = engine.list_btables()['data']
    assert type(list_btables_result) == list
    initial_btable_count = len(list_btables_result)

    test_tablename1, create_btable_result = create_dha()
    test_tablename2, create_btable_result = create_dha()

    list_btables_result = engine.list_btables()['data']
    assert [test_tablename1] in list_btables_result
    assert [test_tablename2] in list_btables_result
    assert len(list_btables_result) == 2 + initial_btable_count

    engine.drop_btable(test_tablename1)
    test_tablename3, create_btable_result = create_dha()
    list_btables_result = engine.list_btables()['data']
    assert [test_tablename1] not in list_btables_result
    assert [test_tablename3] in list_btables_result
    assert [test_tablename2] in list_btables_result

    engine.drop_btable(test_tablename2)
    engine.drop_btable(test_tablename3)

    list_btables_result = engine.list_btables()['data']
    assert len(list_btables_result) == 0 + initial_btable_count


@notimplemented
def test_execute_file():
    pass  # TODO


def test_show_schema():
    test_tablename, _ = create_dha()
    m_c, m_r, t = engine.persistence_layer.get_metadata_and_table(test_tablename)
    cctypes = engine.persistence_layer.get_cctypes(test_tablename)
    assert cctypes[m_c['name_to_idx']['qual_score']] == 'numerical'
    assert cctypes[m_c['name_to_idx']['name']] == 'categorical'

    schema = engine.show_schema(test_tablename)
    cctypes_full = engine.persistence_layer.get_cctypes_full(test_tablename)
    assert sorted([d[1] for d in schema['data']]) == sorted(cctypes_full)
    assert schema['data'][0][0] == 'key'

    mappings = dict(qual_score=dict(cctype='categorical', parameters=None))
    engine.update_schema(test_tablename, mappings)
    cctypes = engine.persistence_layer.get_cctypes(test_tablename)
    assert cctypes[m_c['name_to_idx']['qual_score']] == 'categorical'

    schema = engine.show_schema(test_tablename)
    cctypes_full = engine.persistence_layer.get_cctypes_full(test_tablename)
    assert sorted([d[1] for d in schema['data']]) == sorted(cctypes_full)
    assert schema['data'][0][0] == 'key'


def test_show_models():
    test_tablename, _ = create_dha()
    num_models = 3
    engine.initialize_models(test_tablename, num_models)

    for it in (1, 2):
        analyze_out = engine.analyze(test_tablename, model_indices='all', iterations=1,
                                     background=False)
        model_ids = engine.persistence_layer.get_model_ids(test_tablename)
        assert sorted(model_ids) == range(num_models)
        for i in range(num_models):
            model = engine.persistence_layer.get_models(test_tablename, i)
            assert model['iterations'] == it

        # models should be a list of (id, iterations) tuples.
        models = engine.show_models(test_tablename)['models']
        assert len(models) == num_models
        for iter_id, m in enumerate(models):
            assert iter_id == m[0]
            assert it == m[1]


def test_describe():
    # note that the input data does not have all the values that are in the value maps
    test_tablename, metadata = create_describe_btable()

    bql_string = 'describe c_0 for %s' % test_tablename
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    result = engine.describe(test_tablename, bql_query.columnset)

    assert(len(result['data']) == 1)
    assert(result['data'][0][0] == 'c_0')
    assert(result['data'][0][1] == 'column zero')
    assert(result['data'][0][2] == 'description for column zero')

    # check that M_c reflects the value maps
    metadata = engine.persistence_layer.get_metadata(test_tablename)
    col_0_idx = metadata['M_c']['name_to_idx']['c_0']
    assert(metadata['M_c']['column_metadata'][col_0_idx]['parameters']['cardinality'] == 6)
    assert(len(metadata['M_c']['column_metadata'][col_0_idx]['value_to_code']) == 6)
    assert(len(metadata['M_c']['column_metadata'][col_0_idx]['code_to_value']) == 6)

    assert('6' in result['data'][0][3])  # cardinality


    bql_string = 'describe c_1, c_2, c_3 for %s' % test_tablename
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    result = engine.describe(test_tablename, bql_query.columnset)

    assert(len(result['data']) == 3)
    for row in result['data']:
        assert(len(row) == 4)

    bql_string = 'describe * for %s' % test_tablename
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    result = engine.describe(test_tablename, bql_query.columnset)

    assert(len(result['data']) == 4)
    for row in result['data']:
        assert(len(row) == 4)


def test_update_descriptions_single():
    test_tablename, metadata = create_describe_btable()

    description_proposed = 'Hamish the cat'

    bql_string = 'update description for %s set c_0="%s"' % (test_tablename, description_proposed)
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    _, args, _ = parser.parse_update_descriptions(bql_query)
    result = engine.update_descriptions(test_tablename, args['mappings'])

    column_name_output = result['data'][0][0]
    description_output = result['data'][0][1]

    assert(column_name_output == 'c_0')
    assert(description_output == description_proposed)

    bql_string = 'describe c_0 for %s' % test_tablename
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    result = engine.describe(test_tablename, bql_query.columnset)
    description_updated = result['data'][0][2]

    assert(description_updated == description_proposed)


def test_update_descriptions_multiple():
    test_tablename, metadata = create_describe_btable()

    description_proposed_0 = 'Hamish thh cat'
    description_proposed_1 = 'Winter Ninjaturtle'

    bql_string = 'update descriptions for %s set c_0="%s", c_2="%s"' \
        % (test_tablename, description_proposed_0, description_proposed_1)
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    _, args, _ = parser.parse_update_descriptions(bql_query)
    result = engine.update_descriptions(test_tablename, args['mappings'])

    column_name_output_0 = result['data'][0][0]
    description_output_0 = result['data'][0][1]
    column_name_output_1 = result['data'][1][0]
    description_output_1 = result['data'][1][1]

    assert(column_name_output_0 == 'c_0')
    assert(description_output_0 == description_proposed_0)
    assert(column_name_output_1 == 'c_2')
    assert(description_output_1 == description_proposed_1)

    bql_string = 'describe c_0, c_2 for %s' % test_tablename
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    result = engine.describe(test_tablename, bql_query.columnset)
    description_updated_0 = result['data'][0][2]
    description_updated_1 = result['data'][1][2]

    assert(description_updated_0 == description_proposed_0)
    assert(description_updated_1 == description_proposed_1)


def test_update_short_names_single():
    test_tablename, metadata = create_describe_btable()

    short_name_proposed = 'Hamish'

    bql_string = 'update short name for %s set c_0=%s' % (test_tablename, short_name_proposed)
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    _, args, _ = parser.parse_update_short_names(bql_query)
    result = engine.update_short_names(test_tablename, args['mappings'])

    column_name_output = result['data'][0][0]
    short_name_output = result['data'][0][1]

    assert(column_name_output == 'c_0')
    assert(short_name_output == short_name_proposed)

    bql_string = 'describe c_0 for %s' % test_tablename
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    result = engine.describe(test_tablename, bql_query.columnset)
    short_name_updated = result['data'][0][1]

    assert(short_name_updated == short_name_proposed)

@notimplemented
def test_update_codebook():
    pass # TODO

def test_update_short_names_multiple():
    test_tablename, metadata = create_describe_btable()

    short_name_proposed_0 = 'Hamish'
    short_name_proposed_1 = 'Winter Ninjaturtle'

    bql_string = 'update short names for %s set c_0="%s", c_2="%s"' \
        % (test_tablename, short_name_proposed_0, short_name_proposed_1)
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    _, args, _ = parser.parse_update_short_names(bql_query)
    result = engine.update_short_names(test_tablename, args['mappings'])

    column_name_output_0 = result['data'][0][0]
    short_name_output_0 = result['data'][0][1]
    column_name_output_1 = result['data'][1][0]
    short_name_output_1 = result['data'][1][1]

    assert(column_name_output_0 == 'c_0')
    assert(short_name_output_0 == short_name_proposed_0)
    assert(column_name_output_1 == 'c_2')
    assert(short_name_output_1 == short_name_proposed_1)

    bql_string = 'describe c_0, c_2 for %s' % test_tablename
    bql_query = bql.bql_statement.parseString(bql_string, parseAll=True)
    result = engine.describe(test_tablename, bql_query.columnset)
    short_name_updated_0 = result['data'][0][1]
    short_name_updated_1 = result['data'][1][1]

    assert(short_name_updated_0 == short_name_proposed_0)
    assert(short_name_updated_1 == short_name_proposed_1)


def test_show_diagnostics():
    test_tablename, _ = create_describe_btable()

    with pytest.raises(utils.BayesDBError) as excinfo:
        result = engine.show_diagnostics(test_tablename)
    assert 'No models for btable' in excinfo.value.message

    engine.initialize_models(test_tablename, n_models=2)

    with pytest.raises(utils.BayesDBError) as excinfo:
        result = engine.show_diagnostics(test_tablename)
    assert 'No diagnostics found' in excinfo.value.message

    num_iters = 5
    engine.analyze(test_tablename, iterations=num_iters, background=False)

    results = engine.show_diagnostics(test_tablename)

    # there should be an entry for each diagnostic and also: model id, iterations, time, and
    # logscore
    entry_length = len(diag_utils.single_state_diagnostics) + 4
    assert(len(results['column_labels']) == entry_length)
    assert(len(results['data']) == 2)
    assert(len(results['data'][0]) == entry_length)
    assert(len(results['data'][1]) == entry_length)

    # check values for id and iterations
    assert(results['data'][0][0] == 0)
    assert(results['data'][0][1] == num_iters)

    assert(results['data'][1][0] == 1)
    assert(results['data'][1][1] == num_iters)


@notimplemented
def test_drop_models():
    pass  # TODO


def test_estimate_columns():
    # TODO: add nontrivial cases
    test_tablename, _ = create_dha()
    metadata = engine.persistence_layer.get_metadata(test_tablename)
    all_columns = metadata['M_c']['name_to_idx'].keys()
    engine.initialize_models(test_tablename, 2)

    whereclause = None
    limit = float('inf')
    order_by = False
    name = None
    functions = None
    column_labels = engine.estimate_columns(test_tablename, functions, whereclause, limit, order_by,
                                            name)['column_labels']
    assert column_labels == ['column label', 'column name']

if __name__ == '__main__':
    run_test()

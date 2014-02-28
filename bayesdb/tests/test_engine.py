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

from bayesdb.client import Client
from bayesdb.engine import Engine
engine = Engine()

test_tablenames = None

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
  test_tablename = 'dhatest' + str(int(time.time() * 1000000)) + str(int(random.random()*10000000))
  csv_file_contents = open(path, 'r').read()
  create_btable_result = engine.create_btable(test_tablename, csv_file_contents, None)
  metadata = engine.persistence_layer.get_metadata(test_tablename)
  #import pytest; pytest.set_trace()
  
  global test_tablenames
  test_tablenames.append(test_tablename)
  
  return test_tablename, create_btable_result

def test_create_btable():
  test_tablename, create_btable_result = create_dha()
  assert 'columns' in create_btable_result
  assert 'data' in create_btable_result
  assert 'message' in create_btable_result
  assert len(create_btable_result['data'][0]) == 64 ## 64 is number of columns in DHA dataset
  list_btables_result = engine.list_btables()['list']
  assert test_tablename in list_btables_result
  engine.drop_btable(test_tablename)

def test_drop_btable():
  test_tablename, _ = create_dha()
  list_btables_result = engine.list_btables()['list']
  assert test_tablename in list_btables_result
  engine.drop_btable(test_tablename)
  list_btables_result = engine.list_btables()['list']
  assert test_tablename not in list_btables_result

def test_select():
  test_tablename, _ = create_dha()

  # Test a simple query: select two columns, no limit, no order, no where.
  # Check to make sure types of all inputs are correct, etc.
  columnstring = 'name, qual_score'
  whereclause = ''
  limit = float('inf')
  order_by = False
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert 'columns' in select_result
  assert 'data' in select_result
  assert select_result['columns'] == ['row_id', 'name', 'qual_score']
  ## 307 is the total number of rows in the dataset.
  assert len(select_result['data']) == 307 and len(select_result['data'][0]) == len(select_result['columns'])
  assert type(select_result['data'][0][0]) == int ## type of row_id is int
  t = type(select_result['data'][0][1]) 
  assert (t == unicode) or (t == str) or (t == numpy.string_) ## type of name is unicode or string
  assert type(select_result['data'][0][2]) == float ## type of qual_score is float
  original_select_result = select_result['data']

  ## Test limit: do the same query as before, but limit to 10
  limit = 10
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert len(select_result['data']) == limit

  ## Test order by single column: desc
  ground_truth_ordered_results = sorted(original_select_result, key=lambda t: t[2], reverse=True)[:10]
  order_by = [('qual_score', True)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert select_result['data'] == ground_truth_ordered_results

  ## Test order by single column: asc
  ground_truth_ordered_results = sorted(original_select_result, key=lambda t: t[2])[:10]
  order_by = [('qual_score', False)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert select_result['data'] == ground_truth_ordered_results

  engine.initialize_models(test_tablename, 2)  
  
  # SIMILARITY TO <row> [WITH RESPECT TO <col>]
  # smoke tests
  columnstring = 'name, qual_score, similarity to 5'
  order_by = [('similarity to 5', True)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  columnstring = 'name, qual_score, similarity to 5'
  order_by = [('similarity to 5 with respect to qual_score', True)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  columnstring = 'name, qual_score'
  order_by = [('similarity to 5 with respect to qual_score', True, )]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  
  columnstring = 'name, qual_score, similarity to 5 with respect to name'
  order_by = [('similarity to 5', False)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  columnstring = "name, qual_score, similarity to (name='Albany NY') with respect to qual_score"
  order_by = [('similarity to 5', False)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  columnstring = '*'
  whereclause = 'qual_score > 6'
  order_by = [('similarity to 5 with respect to name', True)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  columnstring = '*'
  # Albany NY's row id is 3
  whereclause = "name='Albany NY'"
  order_by = [('similarity to 5 with respect to name', True)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  
  # TYPICALITY (of row)
  # smoke tests
  columnstring = 'name, qual_score, typicality'
  order_by = False
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  columnstring = 'name, qual_score, typicality'
  order_by = [('typicality', True)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)

  # TODO: test all other single-column functions
  # PROBABILITY <col>=<val>
  # PREDICTIVE PROBABILITY

  # TODO: test all single-column aggregate functions
  
  # TYPICALITY OF <col>
  columnstring = 'typicality of name'
  order_by = [('typicality', True)]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  
  # DEPENDENCE PROBABILITY OF <col> WITH <col> #DEPENDENCE PROBABILITY TO <col>
  # MUTUAL INFORMATION OF <col> WITH <col> #MUTUAL INFORMATION WITH <col>
  # CORRELATION OF <col> WITH <col>
  
  # TODO: test ordering by functions

def test_delete_model():
  pass #TODO

def test_update_schema():
  test_tablename, _ = create_dha()
  m_c, m_r, t = engine.persistence_layer.get_metadata_and_table(test_tablename)
  cctypes = engine.persistence_layer.get_cctypes(test_tablename)
  assert cctypes[m_c['name_to_idx']['qual_score']] == 'continuous'
  assert cctypes[m_c['name_to_idx']['name']] == 'multinomial'
  
  mappings = dict(qual_score='multinomial')
  engine.update_schema(test_tablename, mappings)
  cctypes = engine.persistence_layer.get_cctypes(test_tablename)
  assert cctypes[m_c['name_to_idx']['qual_score']] == 'multinomial'
  
  ## Now test that it doesn't allow name to be continuous
  mappings = dict(name='continuous')
  with pytest.raises(ValueError):
    engine.update_schema(test_tablename, mappings)

def test_save_and_load_models():
  test_tablename, _ = create_dha()
  engine.initialize_models(test_tablename, 3)
  engine.analyze(test_tablename, model_index='all', iterations=1)
  ## note that this won't save the models, since we didn't call this from the client.
  ## engine.save_models actually just turns the models.
  original_models = engine.save_models(test_tablename)
  
  test_tablename2, _ = create_dha()
  engine.load_models(test_tablename2, original_models)
  assert engine.save_models(test_tablename2).values() == original_models.values()

def test_initialize_models():
  test_tablename, _ = create_dha(path='data/dha_missing.csv')     

  engine = Engine(seed=0)
  num_models = 5
  engine.initialize_models(test_tablename, num_models)

  model_ids = engine.persistence_layer.get_model_ids(test_tablename)
  assert sorted(model_ids) == range(num_models)
  for i in range(num_models):
    X_L, X_D, iters = engine.persistence_layer.get_model(test_tablename, i)
    assert iters == 0

def test_analyze():
  test_tablename, _ = create_dha()
  num_models = 3
  engine.initialize_models(test_tablename, num_models)

  for it in (1,2):
    engine.analyze(test_tablename, model_index='all', iterations=1)
    model_ids = engine.persistence_layer.get_model_ids(test_tablename)
    assert sorted(model_ids) == range(num_models)
    for i in range(num_models):
      X_L, X_D, iters = engine.persistence_layer.get_model(test_tablename, i)
      assert iters == it

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
  ## TODO: whereclauses
  test_tablename, _ = create_dha(path='data/dha_missing.csv')

  ## dha_missing has missing qual_score in first 5 rows, and missing name in rows 6-10.
  engine = Engine(seed=0)
  engine.initialize_models(test_tablename, 20)

  columnstring = 'name, qual_score'
  whereclause = ''
  limit = float('inf')
  order_by = False
  numsamples = 30
  confidence = 0
  infer_result = engine.infer(test_tablename, columnstring, '', confidence, whereclause, limit, numsamples, order_by)
  assert 'columns' in infer_result
  assert 'data' in infer_result
  assert infer_result['columns'] == ['row_id', 'name', 'qual_score']
  ## 307 is the total number of rows in the dataset.
  assert len(infer_result['data']) == 307 and len(infer_result['data'][0]) == len(infer_result['columns'])
  assert type(infer_result['data'][0][0]) == int ## type of row_id is int
  t = type(infer_result['data'][0][1])
  assert (t == unicode) or (t == numpy.string_) ## type of name is string
  assert type(infer_result['data'][0][2]) == float ## type of qual_score is float

  all_possible_names = [infer_result['data'][row][1] for row in range(5) + range(10, 307)]
  all_observed_qual_scores = [infer_result['data'][row][2] for row in range(5,307)]

  for row in range(5):
    inferred_name = infer_result['data'][row+5][1]
    inferred_qual_score = infer_result['data'][row][2]
    assert inferred_name in all_possible_names
    assert type(inferred_qual_score) == type(1.2)
    assert inferred_qual_score > min(all_observed_qual_scores)
    assert inferred_qual_score < max(all_observed_qual_scores)

  ## Now, try infer with higher confidence, and make sure that name isn't inferred anymore.
  confidence = 0.9
  infer_result = engine.infer(test_tablename, columnstring, '', confidence, whereclause, limit, numsamples, order_by)

  for row in range(5):
    ## TODO: what do missing values look like? these should be missing
    inferred_name = infer_result['data'][row+5][1]
    inferred_qual_score = infer_result['data'][row][2]
    assert numpy.isnan(inferred_name)
    assert numpy.isnan(inferred_qual_score)

def test_simulate():
  ## TODO: whereclauses
  test_tablename, _ = create_dha()
  engine.initialize_models(test_tablename, 2)
  
  columnstring = 'name, qual_score'
  whereclause = ''
  order_by = False
  numpredictions = 10
  simulate_result = engine.simulate(test_tablename, columnstring, '', whereclause, numpredictions, order_by)
  assert 'columns' in simulate_result
  assert 'data' in simulate_result
  assert simulate_result['columns'] == ['name', 'qual_score']

  assert len(simulate_result['data']) == 10 and len(simulate_result['data'][0]) == len(simulate_result['columns'])
  for row in range(numpredictions):
    t = type(simulate_result['data'][row][0])
    assert (t == unicode) or (t == numpy.string_)
    assert type(simulate_result['data'][row][1]) == float

def test_estimate_pairwise_dependence_probability():
  test_tablename, _ = create_dha()
  engine.initialize_models(test_tablename, 2)
  dep_mat = engine.estimate_pairwise(test_tablename, 'dependence probability')

@pytest.mark.slow
def test_estimate_pairwise_mutual_information():
  ## TODO: speedup! Takes 27 seconds, and this is with 1 sample to estimate mutual information.
  # It definitely takes many more samples to get a good estimate - at least 100.
  test_tablename, _ = create_dha()
  engine.initialize_models(test_tablename, 2)
  mi_mat = engine.estimate_pairwise(test_tablename, 'mutual information')

def test_estimate_pairwise_correlation():
  test_tablename, _ = create_dha()
  engine.initialize_models(test_tablename, 2)
  cor_mat = engine.estimate_pairwise(test_tablename, 'correlation')

def test_list_btables():
  list_btables_result = engine.list_btables()['list']
  assert (type(list_btables_result) == set) or (type(list_btables_result) == list)
  initial_btable_count = len(list_btables_result)
  
  test_tablename1, create_btable_result = create_dha()
  test_tablename2, create_btable_result = create_dha()

  list_btables_result = engine.list_btables()['list']
  assert test_tablename1 in list_btables_result
  assert test_tablename2 in list_btables_result
  assert len(list_btables_result) == 2 + initial_btable_count
  
  engine.drop_btable(test_tablename1)
  test_tablename3, create_btable_result = create_dha()
  list_btables_result = engine.list_btables()['list']  
  assert test_tablename1 not in list_btables_result
  assert test_tablename3 in list_btables_result
  assert test_tablename2 in list_btables_result

  engine.drop_btable(test_tablename2)
  engine.drop_btable(test_tablename3)

  list_btables_result = engine.list_btables()['list']  
  assert len(list_btables_result) == 0 + initial_btable_count


def test_execute_file():
  pass #TODO

def test_show_schema():
  test_tablename, _ = create_dha()
  m_c, m_r, t = engine.persistence_layer.get_metadata_and_table(test_tablename)
  cctypes = engine.persistence_layer.get_cctypes(test_tablename)
  assert cctypes[m_c['name_to_idx']['qual_score']] == 'continuous'
  assert cctypes[m_c['name_to_idx']['name']] == 'multinomial'

  schema = engine.show_schema(test_tablename)
  assert schema['columns'][0] == 'name'
  assert schema['columns'][-4] == 'qual_score'
  assert sorted(schema['data'][0]) == sorted(cctypes)  
  
  mappings = dict(qual_score='multinomial')
  engine.update_schema(test_tablename, mappings)
  cctypes = engine.persistence_layer.get_cctypes(test_tablename)
  assert cctypes[m_c['name_to_idx']['qual_score']] == 'multinomial'
  
  schema = engine.show_schema(test_tablename)
  assert schema['columns'][0] == 'name'
  assert schema['columns'][-4] == 'qual_score'
  assert sorted(schema['data'][0]) == sorted(cctypes)

def test_show_models():
  test_tablename, _ = create_dha()
  num_models = 3
  engine.initialize_models(test_tablename, num_models)

  for it in (1,2):
    analyze_out = engine.analyze(test_tablename, model_index='all', iterations=1)
    model_ids = engine.persistence_layer.get_model_ids(test_tablename)
    assert sorted(model_ids) == range(num_models)
    for i in range(num_models):
      X_L, X_D, iters = engine.persistence_layer.get_model(test_tablename, i)
      assert iters == it

    ## models should be a list of (id, iterations) tuples.
    models = engine.show_models(test_tablename)['models']
    assert analyze_out['models'] == models
    assert len(models) == num_models
    for iter_id, m in enumerate(models):
      assert iter_id == m[0]
      assert it == m[1]
  

def test_show_diagnostics():
  pass #TODO

def test_drop_models():
  pass #TODO

def test_estimate_columns():
  #TODO: add nontrivial cases
  test_tablename, _ = create_dha()
  metadata = engine.persistence_layer.get_metadata(test_tablename)
  all_columns = metadata['M_c']['name_to_idx'].keys()
  engine.initialize_models(test_tablename, 2)
  
  whereclause = ''
  limit = float('inf')
  order_by = None
  name = None
  columnstring = ''
  columns = engine.estimate_columns(test_tablename, columnstring, whereclause, limit, order_by, name)['columns']
  assert columns == all_columns
  
if __name__ == '__main__':
    run_test()

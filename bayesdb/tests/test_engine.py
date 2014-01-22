#
#   Copyright (c) 2010-2013, MIT Probabilistic Computing Project
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
import psycopg2
import pickle
import os
import numpy
import pytest

from bayesdb.engine import Engine
engine = Engine('local')

def create_dha(path='data/dha.csv'):
  test_tablename = 'dhatest' + str(int(time.time() * 1000000))
  csv_file_contents = open(path, 'r').read()
  create_btable_result = engine.create_btable(test_tablename, csv_file_contents, None)
  return test_tablename, create_btable_result

def test_create_btable():
  test_tablename, create_btable_result = create_dha()
  assert 'columns' in create_btable_result
  assert 'data' in create_btable_result
  assert 'message' in create_btable_result
  assert len(create_btable_result['data'][0]) == 64 ## 64 is number of columns in DHA dataset
  list_btables_result = engine.list_btables()
  assert test_tablename in list_btables_result
  engine.drop_btable(test_tablename)

def test_drop_btable():
  test_tablename, _ = create_dha()
  list_btables_result = engine.list_btables()
  assert test_tablename in list_btables_result
  engine.drop_btable(test_tablename)
  list_btables_result = engine.list_btables()
  assert test_tablename not in list_btables_result

def test_select():
  test_tablename, _ = create_dha()
  columnstring = 'name, qual_score'
  whereclause = ''
  limit = float('inf')
  order_by = False
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert 'columns' in select_result
  assert 'data' in select_result
  assert 'message' in select_result
  assert select_result['columns'] == ['row_id', 'name', 'qual_score']
  ## 307 is the total number of rows in the dataset.
  assert len(select_result['data']) == 307 and len(select_result['data'][0]) == len(select_result['columns'])
  assert type(select_result['data'][0][0]) == int ## type of row_id is int
  t = type(select_result['data'][0][1]) 
  assert (t == unicode) or (t == str) or (t == numpy.string_) ## type of name is unicode or string
  assert type(select_result['data'][0][2]) == float ## type of qual_score is float
  original_select_result = select_result['data']

  ## test limit
  limit = 10
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert len(select_result['data']) == limit

  ## test order by single column
  ground_truth_ordered_results = sorted(original_select_result, key=lambda t: t[2], reverse=True)[:10]
  order_by = [('column', {'desc': False, 'column': 'qual_score'})]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert select_result['data'] == ground_truth_ordered_results

  ## test order by desc single column
  """ FAILING!
  ground_truth_ordered_results = sorted(original_select_result, key=lambda t: t[2])[:10]
  order_by = [('column', {'desc': True, 'column': 'qual_score'})]
  select_result = engine.select(test_tablename, columnstring, whereclause, limit, order_by, None)
  assert select_result['data'] == ground_truth_ordered_results
  """

def test_delete_chain():
  pass

def test_update_datatypes():
  test_tablename, _ = create_dha()
  m_c, m_r, t = engine.persistence_layer.get_metadata_and_table(test_tablename)
  cctypes = engine.persistence_layer.get_cctypes(test_tablename)
  assert cctypes[m_c['name_to_idx']['qual_score']] == 'continuous'
  assert cctypes[m_c['name_to_idx']['name']] == 'multinomial'
  
  mappings = dict(qual_score='multinomial')
  engine.update_datatypes(test_tablename, mappings)
  cctypes = engine.persistence_layer.get_cctypes(test_tablename)
  assert cctypes[m_c['name_to_idx']['qual_score']] == 'multinomial'

  ## Now test that it doesn't allow name to be continuous
  mappings = dict(name='continuous')
  with pytest.raises(ValueError):
    engine.update_datatypes(test_tablename, mappings)

def test_export_and_import_samples():
  pass

def test_create_models():
  test_tablename, _ = create_dha()
  engine.create_models(test_tablename, 10)
  model_ids = engine.persistence_layer.get_model_ids(test_tablename)
  assert sorted(model_ids) == range(10)
  for i in range(10):
    X_L, X_D, iters = engine.persistence_layer.get_model(test_tablename, i)
    assert iters == 0

def test_analyze():
  test_tablename, _ = create_dha()
  engine.create_models(test_tablename, 2)

  for it in (1,2):
    engine.analyze(test_tablename, model_index='all', iterations=1)
    model_ids = engine.persistence_layer.get_model_ids(test_tablename)
    assert sorted(model_ids) == range(10)
    for i in range(10):
      X_L, X_D, iters = engine.persistence_layer.get_model(test_tablename, i)
      assert iters == it

def test_infer():
  ## TODO: whereclauses
  test_tablename, _ = create_dha(path='data/dha_missing.csv')
  ## dha_missing has missing qual_score in first 5 rows, and missing name in rows 6-10.
  engine.create_models(test_tablename, 2)

  columnstring = 'name, qual_score'
  whereclause = ''
  limit = float('inf')
  order_by = False
  numsamples = 30
  confidence = 0
  infer_result = engine.infer(test_tablename, columnstring, '', confidence, whereclause, limit, numsamples, order_by)
  assert 'columns' in infer_result
  assert 'data' in infer_result
  assert 'message' in infer_result
  assert infer_result['columns'] == ['row_id', 'name', 'qual_score']
  ## 307 is the total number of rows in the dataset.
  assert len(infer_result['data']) == 307 and len(infer_result['data'][0]) == len(infer_result['columns'])
  assert type(infer_result['data'][0][0]) == int ## type of row_id is int
  assert type(infer_result['data'][0][1]) == unicode ## type of name is unicode string
  assert type(infer_result['data'][0][2]) == float ## type of qual_score is float

  all_possible_names = [infer_result['data'][row][1] for row in range(5) + range(10, 307)]
  all_observed_qual_scores = [qual_score['data'][row][2] for row in range(5,307)]

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
    assert inferred_name not in all_possible_names
    assert type(inferred_qual_score) != type(1.2)


def test_simulate():
  ## TODO: whereclauses
  test_tablename, _ = create_dha()
  ## dha_missing has missing qual_score in first 5 rows, and missing name in rows 6-10.
  engine.create_models(test_tablename, 2)
  
  columnstring = 'name, qual_score'
  whereclause = ''
  order_by = False
  numpredictions = 10
  simulate_result = engine.simulate(test_tablename, columnstring, '', whereclause, numpredictions, order_by)
  assert 'columns' in simulate_result
  assert 'data' in simulate_result
  assert 'message' in simulate_result
  assert simulate_result['columns'] == ['name', 'qual_score']

  assert len(simulate_result['data']) == 10 and len(simulate_result['data'][0]) == len(simulate_result['columns'])
  for row in range(numpredictions):
    assert type(simulate_result['data'][row][0]) == unicode
    assert type(simulate_result['data'][row][1]) == float

def test_estimate_pairwise():
  pass

def test_estimate_dependence_probabilities():
  pass
  
if __name__ == '__main__':
    run_test()

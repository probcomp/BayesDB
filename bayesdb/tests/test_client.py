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
import sys
import pickle
import os
import numpy
import pytest
import random
import shutil
import pandas
from cStringIO import StringIO

import bayesdb.utils as utils
from bayesdb.client import Client
from bayesdb.engine import Engine
import bayesdb.bql_grammar as bql

test_tablenames = None
client = None
test_filenames = None

def setup_function(function):
  global test_tablenames, client, test_filenames
  test_tablenames = []
  test_filenames = []
  # Default upgrade_key_column is None, to let the user choose, but need to avoid
  # user input during testing, so for testing just create a new key column.
  client = Client(testing=True)

def teardown_function(function):
  global tablename, client
  for test_tablename in test_tablenames:
    client.engine.drop_btable(test_tablename)

  for test_filename in test_filenames:
    if os.path.exists(test_filename):
        os.remove(test_filename)

def create_dha(path='data/dha.csv', key_column=0):
  test_tablename = 'dhatest' + str(int(time.time() * 1000000)) + str(int(random.random()*10000000))
  csv_file_contents = open(path, 'r').read()
  client('create btable %s from %s' % (test_tablename, path), debug=True, pretty=False, key_column=key_column)

  global test_tablenames
  test_tablenames.append(test_tablename)

  return test_tablename

def test_drop_btable():
  """
  Test to make sure drop btable prompts the user for confirmation, and responds appropriately when
  given certain input.
  """
  import sys
  from cStringIO import StringIO

  # setup the environment
  backup = sys.stdout
  sys.stdout = StringIO()     # capture output

  # TODO: not being tested at all yet...

  out = sys.stdout.getvalue() # release output
  sys.stdout.close()  # close the stream
  sys.stdout = backup # restore original stdout


def test_btable_list():
  global client, test_filenames

  out = set(client('list btables', pretty=False, debug=True)[0]['btable'])
  init_btable_count = len(out)

  test_tablename1 = create_dha()

  out = set(client('list btables', pretty=False, debug=True)[0]['btable'])
  assert len(out) == 1 + init_btable_count
  assert test_tablename1 in out

  test_tablename2 = create_dha()

  out = set(client('list btables', pretty=False, debug=True)[0]['btable'])
  assert len(out) == 2 + init_btable_count
  assert test_tablename1 in out
  assert test_tablename2 in out

  client('drop btable %s' % test_tablename1, yes=True, debug=True, pretty=False)

  out = set(client('list btables', pretty=False, debug=True)[0]['btable'])
  assert len(out) == 1 + init_btable_count
  assert test_tablename1 not in out
  assert test_tablename2 in out

  ## test to make sure btable list is persisted
  del client
  client = Client()

  out = set(client('list btables', pretty=False, debug=True)[0]['btable'])
  assert len(out) == 1 + init_btable_count
  assert test_tablename1 not in out
  assert test_tablename2 in out


def test_save_and_load_models():
  test_tablename1 = create_dha()
  test_tablename2 = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename1), debug=True, pretty=False)
  #client('analyze %s for 1 iteration' % (test_tablename1), debug=True, pretty=False)
  pkl_path = 'test_models.pkl.gz'
  test_filenames.append(pkl_path)
  client('save models from %s to %s' % (test_tablename1, pkl_path), debug=True, pretty=False)
  original_models = client.engine.save_models(test_tablename1)

  client('load models %s into %s' % (pkl_path, test_tablename2), debug=True, pretty=False)
  new_models = client.engine.save_models(test_tablename2)

  assert new_models.values() == original_models.values()

  # Models are saved with schema now, so check that they can be loaded into a table
  # with the same schema that already has models, and can't be loaded into a table
  # with a different schema that already has models.

  # Should work - schemas are the same and table2 already has models
  client('load models %s into %s' % (pkl_path, test_tablename2), debug=True, pretty=False)

  test_tablename3 = create_dha()
  client('update schema for %s set qual_score = categorical' % (test_tablename3), debug=True, pretty=False)

  # Should work - schemas aren't the same, but table3 doesn't have any models, so the schema will be changed.
  client('load models %s into %s' % (pkl_path, test_tablename3), debug=True, pretty=False)

  test_tablename4 = create_dha()
  client('update schema for %s set qual_score = categorical' % (test_tablename4), debug=True, pretty=False)
  client('initialize 2 models for %s' % (test_tablename4), debug=True, pretty=False)

  # Should fail - schemas aren't the same, and table4 already has models, so the models will be incompatible.
  with pytest.raises(utils.BayesDBError):
    client('load models %s into %s' % (pkl_path, test_tablename4), debug=True, pretty=False)

def test_column_lists():
  """ smoke test """
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)

  cname1 = 'cname1'
  cname2 = 'cname2'
  client('show column lists for %s' % test_tablename, debug=True, pretty=False)
  out = client('estimate columns from %s as %s' % (test_tablename, cname1), debug=True, pretty=False)[0]
  assert type(out) == pandas.DataFrame
  assert (out.columns == ['column label', 'column name']).all()

  client('show column lists for %s' % test_tablename, debug=True, pretty=False)
#TODO grammar update, replace tests after implementing show columns for <column_list>
#  client('show columns %s for %s' % (cname1, test_tablename), debug=True, pretty=False)
#  with pytest.raises(utils.BayesDBColumnListDoesNotExistError):
#    client('show columns %s from %s' % (cname2, test_tablename), debug=True, pretty=False)
  out = client('estimate columns from %s order by typicality limit 5 as %s' % (test_tablename, cname1), debug=True, pretty=False)[0]
  assert out.shape == (5, 3)

  client('estimate columns from %s limit 5 as %s' % (test_tablename, cname2), debug=True, pretty=False)
  client('show column lists for %s' % test_tablename, debug=True, pretty=False)
  # TODO same todo as above
  #  client('show columns %s from %s' % (cname1, test_tablename), debug=True, pretty=False)
  #  client('show columns %s from %s' % (cname2, test_tablename), debug=True, pretty=False)

  tmp = 'asdf_test.png'
  test_filenames.append(tmp)
  if os.path.exists(tmp):
    os.remove(tmp)
  # TODO for columns col_name
  client('estimate pairwise dependence probability from %s for %s save to %s' % (test_tablename, cname1, tmp), debug=True, pretty=False)
  test_ast = bql.bql_statement.parseString('estimate pairwise dependence probability from %s for %s save to %s' % (test_tablename, cname1, tmp),parseAll=True)
  assert test_ast.filename == 'asdf_test.png'
  #TODO current parsing breaks save (probably everything) after "for %s"
  #assert os.path.exists(tmp)

  client('estimate pairwise dependence probability from %s for %s' % (test_tablename, cname2), debug=True, pretty=False)

  client('select %s from %s limit 10' % (cname1, test_tablename), debug=True, pretty=False)
  client('select %s from %s limit 10' % (cname2, test_tablename), debug=True, pretty=False)

  client('infer %s from %s with confidence 0.1 limit 10' % (cname1, test_tablename), debug=True, pretty=False)
  client('infer %s from %s with confidence 0.1 limit 10' % (cname2, test_tablename), debug=True, pretty=False)

  client('simulate %s from %s times 10' % (cname1, test_tablename), debug=True, pretty=False)
  client('simulate %s from %s times 10' % (cname2, test_tablename), debug=True, pretty=False)

  # Test dropping column list
  client('drop column list %s from %s' % (cname1, test_tablename), debug=True, pretty=False)
  client('drop column list %s from %s' % (cname2, test_tablename), debug=True, pretty=False)

  # Assert there are now 0 row lists.
  out = client('show column lists for %s' % test_tablename, debug=True, pretty=False)[0]
  assert out.shape == (0, 1)

def test_simulate():
  """ smoke test """
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)
  # TODO given documentation
  assert len(client("simulate qual_score from %s given name='Albany NY' times 5" % test_tablename, debug=True, pretty=False)[0]) == 5
  assert len(client("simulate qual_score from %s given name='Albany NY' and ami_score = 80 times 5" % test_tablename, debug=True, pretty=False)[0]) == 5

  assert len(client("simulate name from %s given name='Albany NY' and ami_score = 80 times 5" % test_tablename, debug=True, pretty=False)[0]) == 5
  assert len(client("simulate name from %s given name='Albany NY', ami_score = 80 times 5" % test_tablename, debug=True, pretty=False)[0]) == 5
  assert len(client("simulate name from %s given name='Albany NY' AND ami_score = 80 times 5" % test_tablename, debug=True, pretty=False)[0]) == 5
  assert len(client("simulate name from %s given ami_score = 80 times 5" % test_tablename, debug=True, pretty=False)[0]) == 5

def test_estimate_columns():
  """ smoke test """
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)

#  client('estimate columns from %s' % test_tablename, debug=True, pretty=False)

  client('estimate columns from %s where typicality > 1' % test_tablename, debug=True, pretty=False)
  client('estimate columns from %s where typicality > 0' % test_tablename, debug=True, pretty=False)
  client('estimate columns from %s where typicality > 0 order by typicality' % test_tablename, debug=True, pretty=False)
#  client('estimate columns from %s order by typicality limit 5' % test_tablename, debug=True, pretty=False)

  client('estimate columns from %s where dependence probability with qual_score > 0' % test_tablename, debug=True, pretty=False)
  client('estimate columns from %s order by dependence probability with qual_score' % test_tablename, debug=True, pretty=False)
  client('estimate columns from %s order by dependence probability with qual_score limit 5' % test_tablename, debug=True, pretty=False)

  out = client('estimate columns from %s order by correlation with qual_score limit 5' % test_tablename, debug=True, pretty=False)[0]
  scores = out["correlation with qual_score"]
  assert (0 <= scores).all() and (scores <= 1).all()
  out = client('estimate columns from %s where correlation with qual_score > 0 order by correlation with qual_score limit 5' % test_tablename, debug=True, pretty=False)[0]
  scores = out["correlation with qual_score"]
  assert (0 <= scores).all() and (scores <= 1).all()

  client('estimate columns from %s order by mutual information with qual_score limit 5' % test_tablename, debug=True, pretty=False)
  client('estimate columns from %s where mutual information with qual_score > 1 order by typicality' % test_tablename, debug=True, pretty=False)

def test_row_clusters():
  """ smoke test """
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)
  row_lists = client('show row lists for %s' % test_tablename, debug=True, pretty=False)[0]
  assert row_lists.shape == (0, 2)
  client('estimate pairwise row similarity from %s save clusters with threshold 0.1 as rcc' % test_tablename, debug=True, pretty=False)
  row_lists = client('show row lists for %s' % test_tablename, debug=True, pretty=False)[0]
  assert row_lists.shape[0] > 0
  client('select * from %s where key in rcc_0' % test_tablename, debug=True, pretty=False)
  #client("select * from %s where similarity to name='McAllen TX' > 0.5 order by similarity to name='McAllen TX' as mcallenrows" % test_tablename, debug=True, pretty=False)
  #client('select * from %s where key in mcallenrows' % test_tablename, debug=True, pretty=False)

  # Test removing row lists
  client('drop row list rcc from %s' % test_tablename, debug=True, pretty=False)
  out = client('show row lists for %s' % test_tablename, debug=True, pretty=False)[0]
  assert out.shape == (0, 2)

def test_select_whereclause_functions():
  """ smoke test """
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)

  # similarity
  client('select name from %s where similarity to 0 > 0' % (test_tablename), debug=True, pretty=False)
  client('select name from %s where similarity to 0 = 0 order by similarity to 0' % (test_tablename), debug=True, pretty=False)
  client('select name from %s where similarity to 1 with respect to qual_score > 0.01' % (test_tablename), debug=True, pretty=False)
  client('select name from %s where similarity to 1 with respect to qual_score, ami_score > 0.01' % (test_tablename), debug=True, pretty=False)

  # row typicality
  client('select * from %s where typicality > 0.04' % (test_tablename), debug=True, pretty=False)
  client('select *, typicality from %s where typicality > 0.06' % (test_tablename), debug=True, pretty=False)

  # predictive probability
  client("select qual_score from %s where predictive probability of qual_score > 0.01" % (test_tablename), debug=True, pretty=False)
  client("select qual_score from %s where predictive probability of name > 0.01" % (test_tablename), debug=True, pretty=False)

  # probability: aggregate, shouldn't work
  with pytest.raises(utils.BayesDBError):
    client('select qual_score from %s where probability of qual_score = 6 > 0.01' % (test_tablename), debug=True, pretty=False)
  with pytest.raises(utils.BayesDBError):
    client("select qual_score from %s where probability of name='Albany NY' > 0.01" % (test_tablename), debug=True, pretty=False)

def test_model_config():
  test_tablename = create_dha()
  global client, test_filenames

  # test naive bayes
  client('initialize 2 models for %s with config naive bayes' % (test_tablename), debug=True, pretty=False)
  #client('analyze %s for 2 iterations wait' % (test_tablename), debug=True, pretty=False)
  client.engine.analyze(test_tablename, model_indices=[0], iterations=2, background=False)
  dep_mat = client('estimate pairwise dependence probability from %s' % test_tablename, debug=True, pretty=False)[0]['matrix']
  ## assert that all dependencies are _0_ (not 1, because there should only be 1 view and 1 cluster!)
  ## except the diagonal, where we've hardcoded every column to be dependent with itself
  assert numpy.all(dep_mat == numpy.identity(dep_mat.shape[0]))

  # test crp
  with pytest.raises(utils.BayesDBNoModelsError):
    client('drop models from %s' % test_tablename, yes=True, debug=True, pretty=False)
  client('initialize 2 models for %s with config crp mixture' % (test_tablename), debug=True, pretty=False)
  #client('analyze %s for 2 iterations wait' % (test_tablename), debug=True, pretty=False)
  client.engine.analyze(test_tablename, model_indices='all', iterations=2, background=False)
  dep_mat = client('estimate pairwise dependence probability from %s' % test_tablename, debug=True, pretty=False)[0]['matrix']
  ## assert that all dependencies are 1 (because there's 1 view, and many clusters)
  ## (with _very_ low probability, this test may fail due to bad luck)
  assert numpy.all(dep_mat == 1)

  # test crosscat
  with pytest.raises(utils.BayesDBNoModelsError):
    client('drop models from %s' % test_tablename, yes=True, debug=True, pretty=False)
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)
  #client('analyze %s for 2 iterations wait' % (test_tablename), debug=True, pretty=False)
  client.engine.analyze(test_tablename, model_indices='all', iterations=2, background=False)
  dep_mat = client('estimate pairwise dependence probability from %s' % test_tablename, debug=True, pretty=False)[0]['matrix']
  ## assert that all dependencies are not all the same
  assert (not numpy.all(dep_mat == 1)) and (not numpy.all(dep_mat == 0))

  # test that you can't change model config
  with pytest.raises(utils.BayesDBError):
    client.engine.initialize_models(test_tablename, 2, 'crp mixture')


@pytest.mark.xfail
def test_analyze():
  """ test designed to make sure that analyze in background runs correct number of iterations """
  # 1 iteration works fine, but multiple iterations don't.
  # AnalyzeMaster is getting called multiple fucking times.
  # 9, 11, 11, 13 analyze_master calls, and 4 iterations done on every model each of those times (except first one did 3 iters once)
  test_tablename = create_dha(key_column=1) # key column is irrelevant, but let's use it
  global client, test_filenames

  models = 3
  out = client('initialize %d models for %s' % (models, test_tablename), debug=True, pretty=False)[0]

  iterations = 3
  out = client('analyze %s for %d iterations' % (test_tablename, iterations), debug=True, pretty=False)[0]

  out = ''
  while 'not currently being analyzed' not in out:
    out = client('show analyze for %s' % test_tablename, debug=True, pretty=False)[0]['message']

  models = client('show models for %s' % test_tablename, debug=True, pretty=False)[0]['models']
  iters_by_model = [v for k,v in models]
  for i in iters_by_model:
    assert i == iterations

def test_using_models():
  """ smoke test """
  test_tablename = create_dha(path='data/dha_missing.csv')
  global client, test_filenames
  client('initialize 3 models for %s' % (test_tablename), debug=True, pretty=False)

  client('select name from %s using model 1' % test_tablename, debug=True, pretty=False)
  with pytest.raises(utils.BayesDBError):
    client('infer name from %s with confidence 0.1 using models 3' % test_tablename, debug=True, pretty=False)
  with pytest.raises(utils.BayesDBError):
    client("simulate qual_score from %s given name='Albany NY' times 5 using models 3" % test_tablename, debug=True, pretty=False)
  with pytest.raises(utils.BayesDBError):
    client('infer name from %s with confidence 0.1 using models 0-3' % test_tablename, debug=True, pretty=False)

  client('infer name from %s with confidence 0.1 limit 10 using models 2' % test_tablename, debug=True, pretty=False)
  client("simulate qual_score from %s given name='Albany NY' times 5 using models 1-2" % test_tablename, debug=True, pretty=False)
  client('estimate columns from %s limit 5 using models 1-2' % test_tablename, debug=True, pretty=False)
  client('estimate pairwise dependence probability from %s using models 1' % (test_tablename), debug=True, pretty=False)
  client('estimate pairwise row similarity from %s save clusters with threshold 0.1 as rcc using models 1-2' % test_tablename, debug=True, pretty=False)

  client('drop model 0 from %s' % test_tablename, debug=True, pretty=False, yes=True)
  with pytest.raises(utils.BayesDBError):
    client('infer name from %s with confidence 0.1 limit 10 using models 0-2' % test_tablename, debug=True, pretty=False)

def test_select():
  """ smoke test """
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)

  client('select name, qual_score from %s' % (test_tablename), debug=True, pretty=False)
  client('select name, qual_score from %s limit 10' % (test_tablename), debug=True, pretty=False)
  client('select name, qual_score from %s order by qual_score limit 10' % (test_tablename), debug=True, pretty=False)
  client('select name, qual_score from %s order by qual_score ASC limit 10' % (test_tablename), debug=True, pretty=False)
  client('select name, qual_score from %s order by qual_score DESC limit 10' % (test_tablename), debug=True, pretty=False)
  client('select * from %s order by qual_score DESC limit 10' % (test_tablename), debug=True, pretty=False)
  client('select name, qual_score from %s where qual_score > 6' % (test_tablename), debug=True, pretty=False)
  client('select * from %s where qual_score > 6' % (test_tablename), debug=True, pretty=False)
  client("select * from %s where qual_score > 80 and name = 'Albany NY'" % (test_tablename), debug=True, pretty=False)
  client("select * from %s where qual_score > 80 and ami_score > 85" % (test_tablename), debug=True, pretty=False)

  # create a column list to be used in future queries
  client('estimate columns from %s limit 5 as clist' % test_tablename, debug=True, pretty=False)

  # similarity
  client('select name, similarity to 0 from %s' % (test_tablename), debug=True, pretty=False)
  client('select name from %s order by similarity to 0' % (test_tablename), debug=True, pretty=False)
  client('select name, similarity to 0 from %s order by similarity to 0' % (test_tablename), debug=True, pretty=False)
  client('select name, similarity to 0 with respect to name from %s order by similarity to 1 with respect to qual_score' % (test_tablename), debug=True, pretty=False)
  client('select name, similarity to 0 from %s order by similarity to 1 with respect to qual_score, ami_score' % (test_tablename), debug=True, pretty=False)
  client('select name, similarity to 0 from %s order by similarity to 1 with respect to clist' % (test_tablename), debug=True, pretty=False)

  # Add some cases to be sure that referencing row index and column values produces the same output.
  out1 = client('select name, qual_score, similarity to 161 from %s order by similarity to 161 limit 5' % (test_tablename), debug=True, pretty=False)[0]
  out2 = client('select name, qual_score, similarity to name = "McAllen TX" from %s order by similarity to name = "McAllen TX" limit 5' % (test_tablename), debug=True, pretty=False)[0]
  out3 = client('select name, qual_score, similarity to key = 161 from %s order by similarity to key = 161 limit 5' % (test_tablename), debug=True, pretty=False)[0]

  # Assert columns are equal
  for col_idx in range(out1.shape[1]):
    assert (out1.iloc[col_idx] == out2.iloc[col_idx]).all()
    assert (out2.iloc[col_idx] == out3.iloc[col_idx]).all()

  # row typicality
  client('select typicality from %s' % (test_tablename), debug=True, pretty=False)
  client('select *, typicality from %s' % (test_tablename), debug=True, pretty=False)
  client('select typicality from %s order by typicality limit 10' % (test_tablename), debug=True, pretty=False)

  # probability
  # why is this so slow, when predictive probability is really fast? these are _observed_
  # for qual_score (numerical): probability takes 20 times longer than predictive prob (about 5 seconds total for 300 rows)
  # for name (categorical): probability takes extremely long (about 75 seconds for 300 rows)
  #  while predictive probability takes under one second for 300 rows
  st = time.time()
  client('select probability of qual_score = 6 from %s' % (test_tablename), debug=True, pretty=False)
  el = time.time() - st
  st = time.time()
  client("select probability of name='Albany NY' from %s" % (test_tablename), debug=True, pretty=False)
  el2 = time.time() - st

  #client("select name from %s order by probability of name='Albany NY' DESC" % (test_tablename), debug=True, pretty=False)
  # TODO: test that probability function doesn't get evaluated 2x for each row
  #client("select probability of name='Albany NY' from %s order by probability of name='Albany NY' DESC" % (test_tablename), debug=True, pretty=False)

  # predictive probability
  # these are really fast! :) simple predictive probability, unobserved
  client("select predictive probability of qual_score from %s" % (test_tablename), debug=True, pretty=False)
  client("select predictive probability of name from %s" % (test_tablename), debug=True, pretty=False)
  client("select predictive probability of qual_score from %s order by predictive probability of name" % (test_tablename), debug=True, pretty=False)
  client("select predictive probability of qual_score from %s order by predictive probability of qual_score" % (test_tablename), debug=True, pretty=False)

  ## Aggregate functions: can't order by these.

  # mutual information
  client("select name, qual_score, mutual information of name with qual_score from %s" % (test_tablename), debug=True, pretty=False)

  # dependence probability
  client("select dependence probability of name with qual_score from %s" % (test_tablename), debug=True, pretty=False)
  client("select name, qual_score, dependence probability of name with qual_score from %s" % (test_tablename), debug=True, pretty=False)

  # correlation
  client("select name, qual_score, correlation of name with qual_score from %s" % (test_tablename), debug=True, pretty=False)

  # column typicality
  client("select typicality of qual_score, typicality of name from %s" % (test_tablename), debug=True, pretty=False)
  client("select typicality of qual_score from %s" % (test_tablename), debug=True, pretty=False)

  # correlation with missing values
  test_tablename = create_dha(path='data/dha_missing.csv')
  client("select name, qual_score, correlation of name with qual_score from %s" % (test_tablename), debug=True, pretty=False)

def test_into():
  test_tablename = create_dha()
  global client

  client('drop btable test_btable_select', yes=True)

  # Test that select can produce a new btable with INTO, and that it can be analyzed and manipulated like other btables
  client('select name, qual_score from %s limit 5 into test_btable_select' % test_tablename, debug=True, pretty=False)
  out = client('select * from test_btable_select', debug=True, pretty=False)[0]
  assert len(out) == 5
  assert (out.columns == ['key', 'name', 'qual_score']).all()

  client('summarize select * from test_btable_select')
  client('label columns for test_btable_select set qual_score = quality')

  client('initialize 2 models for test_btable_select')
  client('analyze test_btable_select for 2 iterations')
  client('simulate * from test_btable_select times 5')

  client('drop btable test_btable_select', yes=True)

def test_pandas():
  test_tablename = create_dha()
  global client

  # Test that output is a dict if pretty=False and pandas_output=False
  out = client("select name, qual_score from %s limit 10" % (test_tablename), debug=True, pretty=False, pandas_output=False)
  assert type(out[0]) == dict

  # Test that output is pandas DataFrame when pretty=False and a table-like object is returned (pandas_output=True by default)
  out = client("select name, qual_score from %s limit 10" % (test_tablename), debug=True, pretty=False)
  assert type(out[0]) == pandas.DataFrame

  # Test that it still works when no rows are returned
  client("select name, qual_score from %s where qual_score < 0" % (test_tablename), debug=True, pretty=False)

  # Get the returned data frame from the first list element of the previous result.
  test_df = out[0]

  # Test creation of a btable from pandas DataFrame
  client("drop btable %s" % (test_tablename), yes=True)
  client("create btable %s from pandas" % (test_tablename), debug=True, pretty=False, pandas_df=test_df, key_column=1)

def test_summarize():
  test_tablename = create_dha()
  global client

  # Test that the output is a pandas DataFrame when pretty=False
  out = client('summarize select name, qual_score from %s' % (test_tablename), debug=True, pretty=False)[0]
  assert type(out) == pandas.DataFrame
  assert (out.columns == ['', 'name', 'qual_score']).all()

  # Test that stats from summary_describe and summary_freqs made it into the output DataFrame
  # Note that all of these stats won't be present in EVERY summarize output, but all should be in the output
  # from the previous test.
  expected_indices = ['type', 'count', 'unique', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', \
    'mode', 'prob_mode']
  assert all([x in list(out['']) for x in expected_indices])

  # Test that it works on columns of predictive functions.
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)
  client('summarize select correlation of name with qual_score from %s' % (test_tablename), debug=True, pretty=False)

  # Test with fewer than 5 unique values (output should have fewer rows)
  out = client('summarize select name, qual_score from %s limit 3' % (test_tablename), debug=True, pretty=False)[0]
  assert out.shape == (12, 3)

  # Test with no rows
  out = client('summarize select name, qual_score from %s where qual_score < 0' % (test_tablename), debug=True, pretty=False)[0]
  assert out.shape == (0, 3)

  # Test with only a discrete column
  client('summarize select name from %s' % (test_tablename), debug=True, pretty=False)

  # Test with only a numerical column
  client('summarize select qual_score from %s' % (test_tablename), debug=True, pretty=False)

def test_select_where_col_equal_val():
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)
  basic_similarity = client('select * from %s where similarity to 1 > .6 limit 5' % (test_tablename),pretty=False, debug=True)[0]['key']
  col_val_similarity = client('select * from %s where similarity to name = "Akron OH" > .6 limit 5' % (test_tablename),pretty=False, debug=True)[0]['key']
  assert len(basic_similarity) == len(col_val_similarity)

def test_labeling():
  test_tablename = create_dha()
  global client, test_filenames

  client('label columns for %s set name = Name of the hospital, qual_score = Overall quality score' % (test_tablename), debug=True, pretty=False)
  client('show label for %s name, qual_score' % (test_tablename), debug=True, pretty=False)
  client('show label for %s' % (test_tablename), debug=True, pretty=False)

  # Test getting columns from CSV
  client('label columns for %s from data/dha_labels.csv' % (test_tablename), debug=True, pretty=False)

def test_user_metadata():
  test_tablename = create_dha()
  global client, test_filenames

  client('update metadata for %s set data_source = Dartmouth Atlas of Health, url = http://www.dartmouthatlas.org/tools/downloads.aspx' % (test_tablename), debug=True, pretty=False)
  client('update metadata for %s from data/dha_user_metadata.csv' % (test_tablename), debug=True, pretty=False)

  client('show metadata for %s data_source, url' % (test_tablename), debug=True, pretty=False)

  # Test that show metadata also works when no keys are specified
  client('show metadata for %s' % (test_tablename), debug=True, pretty=False)

def test_freq_hist():
  test_tablename = create_dha()
  global client, test_filenames

  # Test that freq and hist work and return a DataFrame
  out = client('freq select qual_score from %s' % (test_tablename), debug=True, pretty=False)[0]
  assert type(out) == pandas.DataFrame
  assert out['qual_score'][0] == 87.5
  assert out['frequency'][0] == 7

  out = client('hist select qual_score from %s' % (test_tablename), debug=True, pretty=False)[0]
  assert type(out) == pandas.DataFrame
  assert out.shape == (10, 4)
  assert out['frequency'][0] == 1

  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)
  client.engine.analyze(tablename=test_tablename, iterations=2, background=False)

  # Results for infer should match select, since there are no missing values
  out = client('freq infer qual_score from %s with confidence 0' % (test_tablename), debug=True, pretty=False)[0]
  assert type(out) == pandas.DataFrame
  assert out['qual_score'][0] == 87.5
  assert out['frequency'][0] == 7

  out = client('hist infer qual_score from %s with confidence 0' % (test_tablename), debug=True, pretty=False)[0]
  assert type(out) == pandas.DataFrame
  assert out.shape == (10, 4)
  assert out['frequency'][0] == 1

  # For simulate, we just have to go by size and expected range
  out = client('freq simulate qual_score from %s times 20' % (test_tablename), debug=True, pretty=False)[0]
  assert out.shape[1] == 3
  assert (out['probability'] < 1).all()

  out = client('hist simulate qual_score from %s times 20' % (test_tablename), debug=True, pretty=False)[0]
  assert out.shape[1] == 4
  assert (out['frequency'] <= 20).all()
  assert (out['probability'] < 1).all()

def test_update_schema():
  test_tablename = create_dha()
  global client, test_filenames

  # Test setting one column to each type other than numerical
  out = client('update schema for %s set qual_score = ignore, ami_score = categorical, pneum_score = cyclic(0, 100)' % (test_tablename), debug=True, pretty=False)[0]
  assert (out['datatype'][out['column'] == 'qual_score'] == 'ignore').all()
  assert (out['datatype'][out['column'] == 'ami_score'] == 'categorical').all()
  assert (out['datatype'][out['column'] == 'pneum_score'] == 'cyclic').all()

  # Test setting categorical with a cardinality parameter
  out = client('update schema for %s set name = categorical(350)' % (test_tablename), debug=True, pretty=False)[0]
  assert (out['datatype'][out['column'] == 'name'] == 'categorical').all()

  # Selecting qual_score should still work even after it's ignored, also should work in where clauses and order by clauses
  client('select qual_score from %s' % (test_tablename), debug=True, pretty=False)
  out = client('select name, qual_score, ami_score from %s where qual_score > 90 order by qual_score' % (test_tablename), debug=True, pretty=False)[0]
  assert (out['qual_score'] > 90).all()
  assert (out['qual_score'] == out['qual_score'].order(ascending=False)).all()

  # Also test where clause with ignored text column
  client('update schema for %s set name = ignore' % (test_tablename), debug=True, pretty=False)
  out = client('select name, qual_score from %s where name = "Albany NY"' % (test_tablename), debug=True, pretty=False)[0]
  assert out.shape == (1, 3)
  assert (out['name'] == "Albany NY").all()

  # Set qual_score, ami_score, pneum_score, and total_fte back to numerical, and select should work again
  client('update schema for %s set qual_score = numerical, ami_score = numerical, pneum_score = numerical, total_fte = numerical' % (test_tablename), debug=True, pretty=False)

  # Set back to ignore, run models, and then estimation shouldn't work for qual_score
  client('update schema for %s set qual_score = ignore' % (test_tablename), debug=True, pretty=False)

  client('initialize 2 models for %s' % (test_tablename), debug=True, pretty=False)

  client.engine.analyze(tablename=test_tablename, iterations=2, background=False)

  with pytest.raises(utils.BayesDBError):
    # Next two statements should fail because they attempt functions on an 'ignore' column
    client('estimate columns from %s order by correlation with qual_score limit 5' % (test_tablename), debug=True, pretty=False)
    client('estimate columns from %s order by dependence probability with qual_score limit 5' % (test_tablename), debug=True, pretty=False)
    # Next two statements should fail because they 1) try to set a new key and 2) try to change the key's type
    client('update schema for %s set name = key' % (test_tablename), debug=True, pretty=False)
    client('update schema for %s set key = numerical' % (test_tablename), debug=True, pretty=False)
    # Next two statements should fail because they set parameters that don't contain the data.
    client('update schema for %s set name = categorical(3)' % (test_tablename), debug=True, pretty=False)
    client('update schema for %s set qual_score = cyclic(0, 10)' % (test_tablename), debug=True, pretty=False)

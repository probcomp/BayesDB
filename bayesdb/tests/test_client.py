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
import pickle
import os
import numpy
import pytest
import random
import shutil

from bayesdb.client import Client
from bayesdb.engine import Engine
engine = Engine('local')

test_tablenames = None
client = None
test_filenames = None

def setup_function(function):
  global test_tablenames, client, test_filenames
  test_tablenames = []
  test_filenames = []
  client = Client()

def teardown_function(function):
  global tablename
  for test_tablename in test_tablenames:
    engine.drop_btable(test_tablename)

  for test_filename in test_filenames:
    if os.path.exists(test_filename):
        os.remove(test_filename)

def create_dha(path='data/dha.csv'):
  test_tablename = 'dhatest' + str(int(time.time() * 1000000)) + str(int(random.random()*10000000))
  csv_file_contents = open(path, 'r').read()
  client('create btable %s from %s' % (test_tablename, 'data/dha.csv'))  
  
  global test_tablenames
  test_tablenames.append(test_tablename)
  
  return test_tablename
    
def test_save_and_load_models():
  test_tablename1 = create_dha()
  test_tablename2 = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename1))
  #client('analyze %s for 1 iteration' % (test_tablename1))
  pkl_path = 'test_models.pkl.gz'
  test_filenames.append(pkl_path)
  client('save models for %s to %s' % (test_tablename1, pkl_path))
  original_models = engine.save_models(test_tablename1)
  
  client('load models %s for %s' % (pkl_path, test_tablename2))
  new_models = engine.save_models(test_tablename1)         

  assert new_models.values() == original_models.values()

def test_estimate_columns():
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename))

  client('estimate columns from %s' % test_tablename)

  client('estimate columns from %s where typicality > 0' % test_tablename)
  client('estimate columns from %s where typicality > 0 order by typicality' % test_tablename)
  client('estimate columns from %s order by typicality limit 5' % test_tablename)

  client('estimate columns from %s where dependence probability with qual_score > 0' % test_tablename)
  client('estimate columns from %s order by dependence probability with qual_score' % test_tablename)
  client('estimate columns from %s order by dependence probability with qual_score limit 5' % test_tablename)

  client('estimate columns from %s order by correlation with qual_score limit 5' % test_tablename)
  client('estimate columns from %s where correlation with qual_score > 0 order by correlation with qual_score limit 5' % test_tablename)  

  client('estimate columns from %s order by mutual information with qual_score limit 5' % test_tablename)
  client('estimate columns from %s where mutual information with qual_score > 0 order by typicality' % test_tablename)

def test_select():
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 2 models for %s' % (test_tablename))

  client('select name, qual_score from %s' % (test_tablename))
  client('select name, qual_score from %s limit 10' % (test_tablename))
  client('select name, qual_score from %s order by qual_score limit 10' % (test_tablename))
  client('select name, qual_score from %s order by qual_score ASC limit 10' % (test_tablename))
  client('select name, qual_score from %s order by qual_score DESC limit 10' % (test_tablename))
  client('select * from %s order by qual_score DESC limit 10' % (test_tablename))
  client('select name, qual_score from %s where qual_score > 6' % (test_tablename))
  client('select * from %s where qual_score > 6' % (test_tablename))

  # similarity
  client('select name, similarity to 0 from %s' % (test_tablename))
  client('select name from %s order by similarity to 0' % (test_tablename))      
  client('select name, similarity to 0 from %s order by similarity to 0' % (test_tablename))
  client('select name, similarity to 0 with respect to name from %s order by similarity to 1 with respect to qual_score' % (test_tablename))        
  client('select name, similarity to 0 from %s order by similarity to 1 with respect to qual_score' % (test_tablename))      

  # row typicality
  client('select typicality from %s' % (test_tablename))
  client('select *, typicality from %s' % (test_tablename))  
  client('select typicality from %s order by typicality limit 10' % (test_tablename))

  # probability
  # why is this so slow, when predictive probability is really fast? these are _observed_
  # for qual_score (continuous): probability takes 20 times longer than predictive prob (about 5 seconds total for 300 rows)
  # for name (multinomial): probability takes extremely long (about 75 seconds for 300 rows)
  #  while predictive probability takes under one second for 300 rows
  client('select probability of qual_score = 6 from %s' % (test_tablename))
  client("select probability of name='Albany NY' from %s" % (test_tablename))

  #client("select name from %s order by probability of name='Albany NY' DESC" % (test_tablename))  
  # TODO: test that probability function doesn't get evaluated 2x for each row
  #client("select probability of name='Albany NY' from %s order by probability of name='Albany NY' DESC" % (test_tablename))

  # predictive probability
  # these are really fast! :) simple predictive probability, unobserved
  client("select predictive probability of qual_score from %s" % (test_tablename))
  client("select predictive probability of name from %s" % (test_tablename))
  client("select predictive probability of qual_score from %s order by predictive probability of name" % (test_tablename))
  client("select predictive probability of qual_score from %s order by predictive probability of qual_score" % (test_tablename))

  ## Aggregate functions: can't order by these.

  # mutual information
  client("select name, qual_score, mutual information of name with qual_score from %s" % (test_tablename))

  # dependence probability
  client("select dependence probability of name with qual_score from %s" % (test_tablename))
  client("select name, qual_score, dependence probability of name with qual_score from %s" % (test_tablename))

  # correlation
  client("select name, qual_score, correlation of name with qual_score from %s" % (test_tablename))

  # column typicality
  client("select typicality of qual_score, typicality of name from %s" % (test_tablename))
  client("select typicality of qual_score from %s" % (test_tablename))

  

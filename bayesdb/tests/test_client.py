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

def test_select():
  test_tablename = create_dha()
  global client, test_filenames
  client('initialize 5 models for %s' % (test_tablename))
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

  # typicality
  client('select typicality from %s' % (test_tablename))
  client('select *, typicality from %s' % (test_tablename))  
  client('select typicality from %s order by typicality limit 10' % (test_tablename))


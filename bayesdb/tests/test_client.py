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

from bayesdb.client import Client
from bayesdb.engine import Engine
engine = Engine('local')

test_tablenames = None
client = None

def setup_function(function):
  global test_tablenames, client
  test_tablenames = []
  client = Client()

def teardown_function(function):
  global tablename
  for test_tablename in test_tablenames:
    engine.drop_btable(test_tablename)

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
  global client
  client('initialize 2 models for %s' % (test_tablename1))
  client('analyze %s for 1 iteration' % (test_tablename1))
  pkl_path = 'test_models.pkl'
  client('save models for %s to %s' % (test_tablename1, pkl_path))
  original_models = engine.save_models(test_tablename1)
  
  client('load models %s for %s' % (pkl_path, test_tablename2))
  new_models = engine.save_models(test_tablename1)         

  assert new_models.values() == original_models.values()

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

def update_cyclic_schema(tablename):
  global client
  for col in range(10):
    client( 'update schema for %s set col_%i=cyclic(0, 6.284)' % (tablename,col), debug=True, pretty=False )

def create_cyclic(path='data/cyclic_test.csv', key_column=0):
  test_tablename = 'cyclictest' + str(int(time.time() * 1000000)) + str(int(random.random()*10000000))
  csv_file_contents = open(path, 'r').read()
  client('create btable %s from %s' % (test_tablename, path), debug=True, pretty=False, key_column=key_column)

  global test_tablenames
  test_tablenames.append(test_tablename)

  return test_tablename

def test_cyclic_initalize():
  """test a few functions with cyclic data"""
  test_tablename = create_cyclic(key_column=0)
  global client, test_filenames

  # update schema
  update_cyclic_schema(test_tablename)

  # intialize model
  models = 3
  out = client('initialize %d models for %s' % (models, test_tablename), debug=True, pretty=False)[0]


def test_cyclic_all_the_things():
  """test a few functions with cyclic data"""
  test_tablename = create_cyclic(key_column=0)
  global client, test_filenames

  # update schema
  update_cyclic_schema(test_tablename)

  # intialize model
  models = 3
  out = client('initialize %d models for %s' % (models, test_tablename), debug=True, pretty=False)[0]

  # analyze
  iterations = 2
  client('analyze %s for %i iterations wait' % (test_tablename, iterations), debug=True, pretty=False)

  # select
  out = client('select col_0 from %s' % (test_tablename), pretty=False)[0]

  # predictive probability
  client('select predictive robability of col_0 from %s LIMIT 10' % (test_tablename), pretty=False)

  # simulate
  client('simulate col_0 from %s times 100' % (test_tablename), pretty=False)

  # simulate w/ GIVEN
  client('simulate col_0 GIVEN col_1 = 3.14 from %s times 100' % (test_tablename), pretty=False)

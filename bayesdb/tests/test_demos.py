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

import os 
import sys 
import pytest

from bayesdb.client import Client

def teardown_function(function):
    for fname in os.listdir('.'):
        if fname[-4] == '.png':
            os.remove(fname)

def run_example(name):
    # Default upgrade_key_column is None, to let the user choose, but need to avoid
    # user input during testing, so default will be to create a new key column.
    client = Client(testing=True)
    file_path = os.path.join('../../examples/%s/%s_analysis.bql' % (name, name))
    results = client(open(file_path, 'r'), yes=True, pretty=False, plots=False, key_column=0)
    for r in results:
        if 'Error' in r or ('error' in r and r['error']):
            raise Exception(str(r))

def test_dha_example():
    run_example('dha')

def test_gss_example():
    run_example('gss')
    
def test_chicago_small_example():
    run_example('chicago_small')

def test_flights_example():
    run_example('flights')

def test_kiva_example():
    run_example('kiva')

def test_employees_example():
    run_example('employees')
    
    

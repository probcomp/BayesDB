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

from bayesdb.engine import Engine
from bayesdb.parser import Parser
engine = Engine('local')
parser = Parser()

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
    assert args == dict(tablename='t', crosscat_column_types=None)
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

def test_estimate_pairwise():
    pass

def test_update_schema():
    pass

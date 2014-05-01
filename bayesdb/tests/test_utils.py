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
import shutil
import pandas

import bayesdb.utils as utils
from bayesdb.client import Client
from bayesdb.engine import Engine
import bayesdb.bql_grammar as bql
'''
Table data for: 
+--------+-----+-----+----+-----+
| row_id |  a  |  b  | c  |  d  |
+--------+-----+-----+----+-----+
|   0    |  1  | 1.0 | we | nan |
|   1    |  2  | 2.0 | we |  2  |
|   2    |  a  | 3.0 | we |  4  |
|   3    |  4  | 3.0 | w  | nan |
|   4    |  4  | 4.0 | w  |  5  |
|   5    |  6  | 5.0 | e  | nan |
|   6    | nan | 6.0 | w  |  3  |
|   7    | nan | 7.0 | sd |  3  |
|   8    | nan | 7.0 | sd |  3  |
+--------+-----+-----+----+-----+

created from csv: 
a,b,c,d
1,1,we,
2,2,we,2
a,3,we,4
4,3,w,
4,4,w,5
6,5,e,
,6,w,3
,7,sd,3
,7,sd,3

'''
test_M_c = {'idx_to_name': {'1': 'b', '0': 'a', '3': 'd', '2': 'c'},
            'column_metadata': [
                    {'code_to_value': {'a': 0, '1': 1, '2': 2, '4': 3, '6': 4}, 
                     'value_to_code': {0: 'a', 1: '1', 2: '2', 3: '4', 4: '6'}, 
                     'modeltype': 'symmetric_dirichlet_discrete'}, 
                    {'code_to_value': {}, 'value_to_code': {}, 
                     'modeltype': 'normal_inverse_gamma'}, 
                    {'code_to_value': {'we': 0, 'e': 1, 'w': 2, 'sd': 3}, 
                     'value_to_code': {0: 'we', 1: 'e', 2: 'w', 3: 'sd'}, 
                     'modeltype': 'symmetric_dirichlet_discrete'}, 
                    {'code_to_value': {'3': 1, '2': 2, '5': 0, '4': 3}, 
                     'value_to_code': {0: '5', 1: '3', 2: '2', 3: '4'}, 
                     'modeltype': 'symmetric_dirichlet_discrete'}], 
            'name_to_idx': {'a': 0, 'c': 2, 'b': 1, 'd': 3}}

test_T = [[1.0, 1.0, 0.0, numpy.nan], 
          [2.0, 2.0, 0.0, 2.0], 
          [0.0, 3.0, 0.0, 3.0], 
          [3.0, 3.0, 2.0, numpy.nan], 
          [3.0, 4.0, 2.0, 0.0], 
          [4.0, 5.0, 1.0, numpy.nan], 
          [numpy.nan, 6.0, 2.0, 1.0], 
          [numpy.nan, 7.0, 3.0, 1.0], 
          [numpy.nan, 7.0, 3.0, 1.0]]

def test_row_id_from_col_value():
    assert utils.row_id_from_col_value('1', 'a', test_M_c, test_T) == 0
    assert utils.row_id_from_col_value('7', 'a', test_M_c, test_T) == None
    assert utils.row_id_from_col_value('1', 'b', test_M_c, test_T) == 0
    assert utils.row_id_from_col_value(1, 'b', test_M_c, test_T) == 0
    assert utils.row_id_from_col_value('1', 'b', test_M_c, test_T) == 0
    try:
        utils.row_id_from_col_value('4', 'a', test_M_c, test_T)
        assert False
    except utils.BayesDBUniqueValueError:
        assert True

def test_string_to_column_type():
    assert utils.string_to_column_type('1', 'a', test_M_c) == '1'
    assert utils.string_to_column_type('1', 'b', test_M_c) == 1
    assert utils.string_to_column_type(1, 'a', test_M_c) == 1

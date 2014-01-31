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

import numpy
import os
import re
import inspect
import ast
import pylab
import matplotlib.cm
import time

import crosscat.utils.data_utils as du
import select_utils

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False    

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_all_column_names_in_original_order(M_c):
    colname_to_idx_dict = M_c['name_to_idx']
    colnames = map(lambda tup: tup[0], sorted(colname_to_idx_dict.items(), key=lambda tup: tup[1]))
    return colnames

def column_string_splitter(columnstring, M_c=None):
    """If '*' is a possible input, M_c must not be None."""
    paren_level = 0
    output = []
    current_column = []

    def end_column(current_column, output):
      if '*' in current_column:
        assert M_c is not None
        output += get_all_column_names_in_original_order(M_c)
      else:
        output.append(''.join(current_column))
      return output
    
    for i,c in enumerate(columnstring):
      if c == '(':
        paren_level += 1
      elif c == ')':
        paren_level -= 1

      if (c == ',' and paren_level == 0):
        output = end_column(current_column, output)
        current_column = []
      else:
        current_column.append(c)
    output = end_column(current_column, output)
    return output

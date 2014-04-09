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

import numpy
import os
import re
import inspect
import ast
import pylab
import matplotlib.cm
import time
import pandas

import data_utils as du
import select_utils
import functions

class BayesDBError(Exception):
    """ Base class for all other exceptions in this module. """
    pass

class BayesDBParseError(BayesDBError):
    def __init__(self, msg=None):
        if msg:
            self.msg = msg
        else:
            self.msg = "BayesDB parsing error. Try using 'help' to see the help menu for BQL syntax."
    
    def __str__(self):
        return self.msg

class BayesDBNoModelsError(BayesDBError):
    def __init__(self, tablename):
        self.tablename = tablename

    def __str__(self):
        return "Btable %s has no models, but this command requires models. Please create models first with INITIALIZE MODELS, and then ANALYZE." % self.tablename

class BayesDBInvalidBtableError(BayesDBError):
    def __init__(self, tablename):
        self.tablename = tablename

    def __str__(self):
        return "Btable %s does not exist. Please create it first with CREATE BTABLE, or view existing btables with LIST BTABLES." % self.tablename

class BayesDBColumnDoesNotExistError(BayesDBError):
    def __init__(self, column, tablename):
        self.column = column
        self.tablename = tablename

    def __str__(self):
        return "Column %s does not exist in btable %s." % (self.column, self.tablename)

class BayesDBColumnListDoesNotExistError(BayesDBError):
    def __init__(self, column_list, tablename):
        self.column_list = column_list
        self.tablename = tablename

    def __str__(self):
        return "Column list %s does not exist in btable %s." % (self.column_list, self.tablename)

class BayesDBRowListDoesNotExistError(BayesDBError):
    def __init__(self, row_list, tablename):
        self.row_list = row_list
        self.tablename = tablename

    def __str__(self):
        return "Row list %s does not exist in btable %s." % (self.row_list, self.tablename)
        
        
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

def infer(M_c, X_L_list, X_D_list, Y, row_id, col_id, numsamples, confidence, engine):
    q = [row_id, col_id]
    out = engine.call_backend('impute_and_confidence', dict(M_c=M_c, X_L=X_L_list, X_D=X_D_list, Y=Y, Q=[q], n=numsamples))
    code, conf = out
    if conf >= confidence:
      return code
    else:
      return None

def check_for_duplicate_columns(column_names):
    column_names_set = set()
    for name in column_names:
        if name in column_names_set:
            raise BayesDBError("Error: Column list has duplicate entries of column: %s" % name)
        column_names_set.add(name)
    

def get_all_column_names_in_original_order(M_c):
    colname_to_idx_dict = M_c['name_to_idx']
    colnames = map(lambda tup: tup[0], sorted(colname_to_idx_dict.items(), key=lambda tup: tup[1]))
    return colnames

def summarize_table(data, columns, M_c):
    """
    Returns a summary of the data.
    Input: data is a list of lists, of raw data values about to be shown to the user.
    Input: columns is a list of column names, as they will be displayed to the user. Note
    that some column names may be things like "row_id" or predictive functions, not actually
    columns.

    Return: columns should be the same, except with another column prepended called like "summaries" or something.
    Return: data should be summaries now.
    """

    # Construct a pandas.DataFrame out of data and columns
    df = pandas.DataFrame(data=data, columns=columns)

    # Remove row_id column since summary stats of row_id are meaningless - add it back at the end
    df.drop(['row_id'], inplace=True, axis=1)

    # Run pandas.DataFrame.describe() on each column - it'll compute every stat that it can for each column,
    # depending on its type (assume it's not a problem to overcompute here - for example, computing a mean on a 
    # discrete variable with numeric values might not have meaning, but it's easier just to do it and 
    # leave interpretation to the user, rather than try to figure out what's meaningful, especially with 
    # columns that are the result of predictive functions.
    summary_describe = df.apply(lambda x: x.describe())

    # If there were discrete columns, remove 'top' and 'freq' rows, because we'll replace those
    # with the mode and empirical probabilities
    if 'top' in summary_describe.index and 'freq' in summary_describe.index:
        summary_describe.drop(['top', 'freq'], inplace=True)

    # Function to calculate the most frequent values for each column
    def get_column_freqs(x, n=5):
        """
        Function to return most frequent n values of each column of the DataFrame being summarized.
        Input: a DataFrame column, by default as Series type

        Return: most frequent n values in x. Fill with numpy.nan if fewer than n unique values exist.
        """
        x_freqs  = x.value_counts()
        x_probs  = list(x_freqs / len(x))
        x_values = list(x_freqs.index)

        if len(x_values) > n:
            x_probs = x_probs[:n]
            x_values = x_values[:n]

        # Create index labels ('mode1/2/3/... and prob_mode1/2/3...')
        x_range = range(1, len(x_values) + 1)
        x_index = ['mode' + str(i) for i in x_range]
        x_index += ['prob_mode' + str(i) for i in x_range]

        # Combine values and probabilities into a single list
        x_values.extend(x_probs)

        return pandas.Series(data = x_values, index = x_index)

    summary_freqs = df.apply(lambda x: get_column_freqs(x))

    # Replace 'top' in row index with 'mode' for clearer meaning

    # Attach continuous and discrete summaries along row axis (unaligned values will be assigned NaN)
    summary_data = pandas.concat([summary_describe, summary_freqs], axis=0)

    # Insert column of stat descriptions - allow duplication of column name in case user's data has a column named stat
    summary_data.insert(0, 'stat', summary_data.index, allow_duplicates=True)

    # Recreate row_index for summary output
    summary_data.insert(0, 'row_index', range(summary_data.shape[0]), allow_duplicates=True)

    data = summary_data.to_records(index=False)
    columns = list(summary_data.columns)
    return data, columns

def column_string_splitter(columnstring, M_c=None, column_lists=None):
    """
    If '*' is a possible input, M_c must not be None.
    If column_lists is not None, all column names are attempted to be expanded as a column list.
    """
    paren_level = 0
    output = []
    current_column = []

    def end_column(current_column, output):
      if '*' in current_column:
        assert M_c is not None
        output += get_all_column_names_in_original_order(M_c)
      else:
        current_column_name = ''.join(current_column)
        if column_lists and current_column_name in column_lists.keys():
            ## First, check if current_column is a column_list
            output += column_lists[current_column_name]
        else:
            ## If not, then it is a normal column name: append it.            
            output.append(current_column_name.strip())
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

    

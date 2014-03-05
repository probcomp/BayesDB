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

import data_utils as du
import select_utils
import functions

class BayesDBError(Exception):
    """ Base class for all other exceptions in this module. """
    def __str__(self):
        return "BayesDB internal error. Try using 'help' to see the help menu."

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

def get_all_column_names_in_original_order(M_c):
    colname_to_idx_dict = M_c['name_to_idx']
    colnames = map(lambda tup: tup[0], sorted(colname_to_idx_dict.items(), key=lambda tup: tup[1]))
    return colnames

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

def generate_pairwise_matrix(col_function_name, X_L_list, X_D_list, M_c, T, tablename='', confidence=None, limit=None, submatrix=False, engine=None, column_names=None, component_threshold=None):
    """ Compute a matrix. If using a function that requires engine (currently only
    mutual information), engine must not be None. """

    # Get appropriate function
    assert len(X_L_list) == len(X_D_list)
    if col_function_name == 'mutual information':
      if len(X_L_list) == 0:
        return {'message': 'You must initialize models before computing mutual information.'}    
      col_function = functions._mutual_information
    elif col_function_name == 'dependence probability':
      if len(X_L_list) == 0:
        return {'message': 'You must initialize models before computing dependence probability.'}
      col_function = functions._dependence_probability
    elif col_function_name == 'correlation':
      col_function = functions._correlation
    else:
      raise BayesDBParseError('Invalid column function: %s' % col_function_name)

    # If using a subset of the columns, get the appropriate names, and figure out their indices.
    if column_names:
        num_cols = len(column_names)
        column_indices = [M_c['name_to_idx'][name] for name in column_names]
    else:
        num_cols = len(X_L_list[0]['column_partition']['assignments'])
        column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
        column_indices = range(num_cols)
    column_names = numpy.array(column_names)
    
    # Compute unordered matrix: evaluate the function for every pair of columns
    # Shortcut: assume all functions are symmetric between columns, only compute half.
    num_latent_states = len(X_L_list)
    z_matrix = numpy.zeros((num_cols, num_cols))
    for i, orig_i in enumerate(column_indices):
      for j in range(i, num_cols):
        orig_j = column_indices[j]
        func_val = col_function((orig_i, orig_j), None, None, M_c, X_L_list, X_D_list, T, engine)
        z_matrix[i][j] = func_val
        z_matrix[j][i] = func_val

    # Hierarchically cluster columns.
    import hcluster
    Y = hcluster.pdist(z_matrix)
    Z = hcluster.linkage(Y)
    pylab.figure()
    hcluster.dendrogram(Z)
    intify = lambda x: int(x.get_text())
    reorder_indices = map(intify, pylab.gca().get_xticklabels())
    pylab.clf() ## use instead of close to avoid error spam
    # reorder the matrix
    z_matrix_reordered = z_matrix[:, reorder_indices][reorder_indices, :]
    column_names_reordered = column_names[reorder_indices]

    # If component_threshold isn't none, then we want to return all the connected components
    # of columns: columns are connected if their edge weight is above the threshold.
    # Just do a search, starting at each column id.
    if component_threshold is not None:
        from collections import defaultdict
        components = [] # list of lists (conceptually a set of sets, but faster here)

        # Construct graph, in the form of a neighbor dictionary
        neighbors_dict = defaultdict(list)
        for i in range(num_cols):
            for j in range(i+1, num_cols):
                if z_matrix[i][j] > component_threshold:
                    neighbors_dict[i].append(j)
                    neighbors_dict[j].append(i)

        # Outer while loop: make sure every column has been visited
        unvisited = set(range(num_cols))
        while(len(unvisited) > 0):
            component = []
            stack = [unvisited.pop()]
            while(len(stack) > 0):
                cur = stack.pop()
                component.append(cur)                
                neighbors = neighbors_dict[cur]
                for n in neighbors:
                    if n in unvisited:
                        stack.append(n)
                        unvisited.remove(n)                        
            if len(component) > 1:
                components.append(component)
                
        # Now, convert the components from their z_matrix indices to their btable indices
        new_comps = []
        for comp in components:
            new_comps.append([column_indices[c] for c in comp])
        components = new_comps
            
    title = 'Pairwise column %s for %s' % (col_function_name, tablename)

    ret = dict(
      matrix=z_matrix_reordered,
      column_names=column_names_reordered,
      title=title,
      message = "Created " + title
      )
    if component_threshold is not None:
        ret['components'] = components
    return ret
    

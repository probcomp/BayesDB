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
import utils
import parser

def parse_pairwise_function(function_name, column=True, M_c=None, column_lists={}): ##TODO move to parser
    if column:
        if function_name == 'mutual information':
            return functions._mutual_information
        elif function_name == 'dependence probability':
            return functions._dependence_probability
        elif function_name == 'correlation':
            return functions._correlation
        else:
            raise utils.BayesDBParseError('Invalid column function: %s' % function_name)
    else:
        # TODO: need to refactor to support similarity with respect to column, because then we need to parse
        # and return the column id here.
        ##TODO temporary hack - move to parser maybe combine with parse_functions
        p = parser.Parser()
        _, target_columns = p.get_args_similarity(function_name, M_c, None, M_c, None, column_lists)
        if target_columns is None:
            return (functions._similarity, None)
        elif type(target_columns) == list:
            return (functions._similarity, target_columns)
        else:
            raise utils.BayesDBParseError('Invalid row function: %s' % function_name)

def get_columns(column_names, M_c): ##TODO move to parser or utils
    # If using a subset of the columns, get the appropriate names, and figure out their indices.
    if column_names is not None:
        column_indices = [M_c['name_to_idx'][name] for name in column_names]
    else:
        num_cols = len(M_c['name_to_idx'].keys())
        column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
        column_indices = range(num_cols)
    column_names = numpy.array(column_names)
    return column_names, column_indices

def compute_raw_column_pairwise_matrix(function, X_L_list, X_D_list, M_c, T, engine, column_indices=None, numsamples=None):
    # Compute unordered matrix: evaluate the function for every pair of columns
    # Shortcut: assume all functions are symmetric between columns, only compute half.
    num_cols = len(column_indices)
    matrix = numpy.zeros((num_cols, num_cols))
    for i, orig_i in enumerate(column_indices):
        for j in range(i, num_cols):
            orig_j = column_indices[j]
            func_val = function((orig_i, orig_j), None, None, M_c, X_L_list, X_D_list, T, engine, numsamples)
            matrix[i][j] = func_val
            matrix[j][i] = func_val
    return matrix

def compute_raw_row_pairwise_matrix(function, arg, X_L_list, X_D_list, M_c, T, engine, row_indices=None, numsamples=None):
    # TODO: currently assume that the only function possible is similarity
    if row_indices is None:
        row_indices = range(len(T))
    num_rows = len(row_indices)
    matrix = numpy.zeros((num_rows, num_rows))
    for i, orig_i in enumerate(row_indices):
        for j in range(i, num_rows):
            orig_j = row_indices[j]
            func_val = function((orig_i, arg), orig_j, None, M_c, X_L_list, X_D_list, T, engine, numsamples)
            matrix[i][j] = func_val
            matrix[j][i] = func_val
    return matrix

def reorder_indices_by_cluster(matrix):
    # Hierarchically cluster columns.
    from scipy.spatial.distance import pdist
    from scipy.cluster.hierarchy import linkage, dendrogram
    Y = pdist(matrix)
    Z = linkage(Y)
    pylab.figure()
    dendrogram(Z)
    intify = lambda x: int(x.get_text())
    reorder_indices = map(intify, pylab.gca().get_xticklabels())
    pylab.clf() ## use instead of close to avoid error spam
    matrix_reordered = matrix[:, reorder_indices][reorder_indices, :]    
    return matrix_reordered, reorder_indices

def get_connected_clusters(matrix, cluster_threshold):
    # If cluster_threshold isn't none, then we want to return all the connected clusters
    # of columns: columns are connected if their edge weight is above the threshold.
    # Just do a search, starting at each column id.

    from collections import defaultdict
    clusters = [] # list of lists (conceptually a set of sets, but faster here)

    # Construct graph, in the form of a neighbor dictionary
    neighbors_dict = defaultdict(list)
    for i in range(matrix.shape[0]):
        for j in range(i+1, matrix.shape[0]):
            if matrix[i][j] > cluster_threshold:
                neighbors_dict[i].append(j)
                neighbors_dict[j].append(i)

    # Outer while loop: make sure every column has been visited
    unvisited = set(range(matrix.shape[0]))
    while(len(unvisited) > 0):
        cluster = []
        stack = [unvisited.pop()]
        while(len(stack) > 0):
            cur = stack.pop()
            cluster.append(cur)
            neighbors = neighbors_dict[cur]
            for n in neighbors:
                if n in unvisited:
                    stack.append(n)
                    unvisited.remove(n)                        
        if len(cluster) > 1:
            clusters.append(cluster)
    return clusters

def generate_pairwise_column_matrix(function_name, X_L_list, X_D_list, M_c, T, tablename='', limit=None, engine=None, column_names=None, cluster_threshold=None, numsamples=None):
    """
    Compute a matrix. In using a function that requires engine (currently only
    mutual information), engine must not be None.
    """

    # Get appropriate function
    function = parse_pairwise_function(function_name, column=True, M_c=M_c)

    # Get appropriate column information from column_names
    column_names, column_indices = get_columns(column_names, M_c)

    # Actually compute each function between each pair of columns
    matrix = compute_raw_column_pairwise_matrix(function, X_L_list, X_D_list, M_c, T, engine, column_indices, numsamples)

    if cluster_threshold is not None:
        # clusters is a list of lists, where the inner list contains the ids (into the matrix)
        # of the columns in each cluster.
        clusters = get_connected_clusters(matrix, cluster_threshold)
        
        # Now, convert the clusters from their matrix indices to their btable indices
        new_comps = []
        for comp in clusters:
            new_comps.append([column_indices[c] for c in comp])
        clusters = new_comps
    else:
        clusters = None

    # reorder the matrix
    matrix, reorder_indices = reorder_indices_by_cluster(matrix)
    column_names_reordered = column_names[reorder_indices]
            
    return matrix, column_names_reordered, clusters

def generate_pairwise_row_matrix(function_name, X_L_list, X_D_list, M_c, T, tablename='', engine=None, row_indices=None, cluster_threshold=None, column_lists={}, numsamples=None):
    """
    Compute a matrix. In using a function that requires engine (currently only
    mutual information), engine must not be None.
    """

    # Get appropriate function
    function, arg = parse_pairwise_function(function_name, column=False, M_c=M_c, column_lists=column_lists)

    # Get appropriate row list
    if row_indices is None:
        row_indices = numpy.array(range(len(T)))
    else:
        row_indices = numpy.array(row_indices)

    # Actually compute each function between each pair of columns
    matrix = compute_raw_row_pairwise_matrix(function, arg, X_L_list, X_D_list, M_c, T, engine, row_indices, numsamples)

    if cluster_threshold is not None:
        # clusters is a list of lists, where the inner list contains the ids (into the matrix)
        # of the columns in each cluster.
        clusters = get_connected_clusters(matrix, cluster_threshold)
        
        # Now, convert the clusters from their matrix indices to their btable indices
        new_comps = []
        for comp in clusters:
            new_comps.append([row_indices[c] for c in comp])
        clusters = new_comps
    else:
        clusters = None

    # reorder the matrix
    matrix, reorder_indices = reorder_indices_by_cluster(matrix)
    row_indices_reordered = row_indices[reorder_indices]
            
    return matrix, row_indices_reordered, clusters
    

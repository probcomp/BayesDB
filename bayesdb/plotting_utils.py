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

import numpy as np
import os
import pylab
import matplotlib.cm
import pandas as pd

import utils
import functions
import data_utils as du

import math

import pdb

KDE = True

def plot_general_histogram(colnames, data, M_c, filename=None):
    '''
    colnames: list of column names
    data: list of tuples (first list is a list of rows, so each inner tuples is a row)
    colnames = ['name', 'age'], data = [('bob',37), ('joe', 39),...]
    '''
#    pdb.set_trace()
    fig, ax = pylab.subplots()
    parsed_data = parse_data_for_hist(colnames, data, M_c)
    if parsed_data['datatype'] == 'mult1D':
        print 'mult1D'
        labels = parsed_data['labels']
        datapoints = parsed_data['data']
        num_vals = len(labels)
        ind = np.arange(num_vals)
        width = .5
        rects = ax.barh(ind, datapoints, width)
        ax.set_yticks(ind+width)
        ax.set_yticklabels(labels)
    elif parsed_data['datatype'] == 'cont1D':
        datapoints = parsed_data['data']
        if KDE:
            from scipy.stats import kurtosis
            doanes = lambda dataq: int(1 + math.log(len(dataq)) + math.log(1 + kurtosis(dataq) * (len(dataq) / 6.) ** 0.5))
            series = pd.Series(datapoints)
            series.hist(bins=doanes(series.dropna()), normed=True, color='lightseagreen')
            series.dropna().plot(kind='kde', xlim=(0,100), style='r--') #Should be changed from hardcoded 100
        else:
            ax.hist(parsed_data['data'], orientation='horizontal')
    else:
        return
    if filename:
        pylab.savefig(filename)
    else:
        fig.show()

def parse_data_for_hist(colnames, data, M_c):
    output = {}
    if len(colnames) - 1 == 1:
        col_idx = M_c['name_to_idx'][colnames[1]]
        if M_c['column_metadata'][col_idx]['modeltype'] == 'symmetric_dirichlet_discrete':
            str_data = [x[1] for x in data]
            unique_labels = list(set(str_data))
            np_str_data = np.array(str_data)
            counts = []
            for label in unique_labels:
                counts.append(sum(np_str_data==label))
            output['datatype'] = 'mult1D'
            output['labels'] = unique_labels
            output['data'] = counts
        elif M_c['column_metadata'][col_idx]['modeltype'] == 'normal_inverse_gamma':
            output['datatype'] = 'cont1D'
            output['data'] = np.array([x[1] for x in data])
    elif len(colnames) - 1 == 2:
        output['datatype'] = '2D'
    else:
        output['datatype'] = None
    return output

def plot_matrix(matrix, column_names, title='', filename=None):
    # actually create figure
    fig = pylab.figure()
    fig.set_size_inches(16, 12)
    pylab.imshow(matrix, interpolation='none',
                 cmap=matplotlib.cm.gray_r, vmin=0, vmax=1)
    pylab.colorbar()
    pylab.gca().set_yticks(range(len(column_names)))
    pylab.gca().set_yticklabels(column_names, size='small')
    pylab.gca().set_xticks(range(len(column_names)))
    pylab.gca().set_xticklabels(column_names, rotation=90, size='small')
    pylab.title(title)
    if filename:
        pylab.savefig(filename)
    else:
        fig.show()


def _create_histogram(M_c, data, columns, mc_col_indices, filename):
  dir=S.path.web_resources_data_dir
  full_filename = os.path.join(dir, filename)
  num_rows = data.shape[0]
  num_cols = data.shape[1]
  #
  pylab.figure()
  # col_i goes from 0 to number of predicted columns
  # mc_col_idx is the original column's index in M_c
  for col_i in range(num_cols):
    mc_col_idx = mc_col_indices[col_i]
    data_i = data[:, col_i]
    ax = pylab.subplot(1, num_cols, col_i, title=columns[col_i])
    if M_c['column_metadata'][mc_col_idx]['modeltype'] == 'normal_inverse_gamma':
      pylab.hist(data_i, orientation='horizontal')
    else:
      str_data = [du.convert_code_to_value(M_c, mc_col_idx, code) for code in data_i]
      unique_labels = list(set(str_data))
      np_str_data = np.array(str_data)
      counts = []
      for label in unique_labels:
        counts.append(sum(np_str_data==label))
      num_vals = len(M_c['column_metadata'][mc_col_idx]['code_to_value'])
      rects = pylab.barh(range(num_vals), counts)
      heights = np.array([rect.get_height() for rect in rects])
      ax.set_yticks(np.arange(num_vals) + heights/2)
      ax.set_yticklabels(unique_labels)
  pylab.tight_layout()
  pylab.savefig(full_filename)


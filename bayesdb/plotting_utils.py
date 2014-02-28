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
import pylab as p
import os
from matplotlib.colors import LogNorm
from matplotlib.colors import Normalize
import matplotlib.cm
import pandas as pd
import numpy
import utils
import functions
import data_utils as du
import math
from scipy.stats import kurtosis


def plot_general_histogram(colnames, data, M_c, filename=None):
    '''
    colnames: list of column names
    data: list of tuples (first list is a list of rows, so each inner tuples is a row)
    colnames = ['name', 'age'], data = [('bob',37), ('joe', 39),...]
    '''

    p.figure()
    parsed_data = parse_data_for_hist(colnames, data, M_c)

    if parsed_data['datatype'] == 'mult1D':
        labels = parsed_data['labels']
        datapoints = parsed_data['data']
        num_vals = len(labels)
        ind = np.arange(num_vals)
        width = .5
        p.barh(ind, datapoints, width, color='lightseagreen')
        p.yticks(ind + width/2, labels)
        p.ylabel(parsed_data['axis_label'])

    elif parsed_data['datatype'] == 'cont1D':
        datapoints = parsed_data['data']
        from scipy.stats import kurtosis
        doanes = lambda dataq: int(1 + math.log(len(dataq)) + math.log(1 + kurtosis(dataq) * (len(dataq) / 6.) ** 0.5))
        series = pd.Series(datapoints)
        series.hist(bins=doanes(series.dropna()), normed=True, color='lightseagreen')
        series.dropna().plot(kind='kde', style='r--') 
        p.xlabel(parsed_data['axis_label'])
        
    elif parsed_data['datatype'] == 'contcont':
        p.hist2d(parsed_data['data_x'], parsed_data['data_y'], bins=max(len(parsed_data['data_x'])/200,40), norm=LogNorm(), cmap='cool')
        p.colorbar()
        p.ylabel(parsed_data['axis_label_y'])
        p.xlabel(parsed_data['axis_label_x'])

        
    elif parsed_data['datatype'] == 'multmult':
        unique_xs = parsed_data['labels_x']
        unique_ys = parsed_data['labels_y']
        dat = parsed_data['data']
        norm_a = Normalize(vmin=dat.min(), vmax=dat.max()) 
        p.imshow(parsed_data['data'],norm=Normalize(), interpolation='nearest',  cmap=matplotlib.cm.cool)
        p.xticks(range(len(unique_xs)), unique_xs)
        p.yticks(range(len(unique_ys)), unique_ys)
        p.colorbar()
        p.ylabel(parsed_data['axis_label_y'])
        p.xlabel(parsed_data['axis_label_x'])

    elif parsed_data['datatype'] == 'multcont':
        raise Exception('multinomial by continous plots not implemeneted at the moment.')
        #df = pd.DataFrame(dict(score = np.array(parsed_data['values']), group = np.array(parsed_data['groups'])))
        #violinplot(df.score, df.group);
        #p.ylabel(parsed_data['axis_label_y'])
        #p.xlabel(parsed_data['axis_label_x'])

    else:
        raise Exception('Unexpected data type')
    p.suptitle(parsed_data['title'])
    if filename:
        p.savefig(filename)
        p.close()
    else:
        p.show()

def parse_data_for_hist(colnames, data, M_c):
    data_c = []
    for i in data:
        no_nan = True
        for j in i:
            if isinstance(j, float) and math.isnan(j):
                no_nan = False
        if no_nan:
            data_c.append(i)
    output = {}
    columns = colnames[:]
    data_no_id = [] #This will be the data with the row_ids removed if present
    if colnames[0] == 'row_id':
        columns.pop(0)

    if len(columns) == 1:
        if colnames[0] == 'row_id':
            data_no_id = [x[1] for x in data_c]
        else:
            data_no_id = [x[0] for x in data_c]
        output['axis_label'] = columns[0]
        output['title'] = columns[0]
        col_idx = M_c['name_to_idx'][columns[0]]
        if M_c['column_metadata'][col_idx]['modeltype'] == 'symmetric_dirichlet_discrete':
            unique_labels = sort_mult_list(list(set(data_no_id)))

            np_data = np.array(data_no_id)
            counts = []
            for label in unique_labels:
                counts.append(sum(np_data==str(label)))
            output['datatype'] = 'mult1D'
            output['labels'] = unique_labels
            output['data'] = counts

        elif M_c['column_metadata'][col_idx]['modeltype'] == 'normal_inverse_gamma':
            output['datatype'] = 'cont1D'
            output['data'] = np.array(data_no_id)

    elif len(columns) == 2:
        if colnames[0] == 'row_id':
            data_no_id = [(x[1], x[2]) for x in data_c]
        else:
            data_no_id = [(x[0], x[1]) for x in data_c]

        col_idx_1 = M_c['name_to_idx'][columns[0]]
        col_idx_2 = M_c['name_to_idx'][columns[1]]
        types = (M_c['column_metadata'][col_idx_1]['modeltype'], M_c['column_metadata'][col_idx_2]['modeltype'])
        
        output['axis_label_x'] = columns[0]
        output['axis_label_y'] = columns[1]
        output['title'] = columns[0] + ' -versus- ' + columns[1]
 
        if M_c['column_metadata'][col_idx_1]['modeltype'] == 'normal_inverse_gamma' and M_c['column_metadata'][col_idx_2]['modeltype'] == 'normal_inverse_gamma':
            output['datatype'] = 'contcont'
            output['data_x'] = [x[0] for x in data_no_id]
            output['data_y'] = [x[1] for x in data_no_id]

        elif M_c['column_metadata'][col_idx_1]['modeltype'] == 'symmetric_dirichlet_discrete' and M_c['column_metadata'][col_idx_2]['modeltype'] == 'symmetric_dirichlet_discrete':
            counts = {}
            for i in data_no_id:
                if i in counts:
                    counts[i]+=1
                else:
                    counts[i]=1
            unique_xs = sort_mult_list(list(M_c['column_metadata'][col_idx_1]['code_to_value'].keys()))
            unique_ys = sort_mult_list(list(M_c['column_metadata'][col_idx_2]['code_to_value'].keys()))
            counts_array = numpy.zeros(shape=(len(unique_ys), len(unique_xs)))
            for i in counts:
                counts_array[M_c['column_metadata'][col_idx_2]['code_to_value'][i[1]]][M_c['column_metadata'][col_idx_1]['code_to_value'][i[0]]] = float(counts[i])
            output['datatype'] = 'multmult'
            print counts_array
            output['data'] = counts_array
            output['labels_x'] = unique_xs
            output['labels_y'] = unique_ys

        elif 'normal_inverse_gamma' in types and 'symmetric_dirichlet_discrete' in types:
            output['datatype'] = 'multcont'
            if types[0] == 'normal_inverse_gamma':                
                data_no_id = sort_mult_tuples(data_no_id, 1)
                output['groups'] = [x[1] for x in data_no_id]
                output['values'] = [x[0] for x in data_no_id]
                temp = output['axis_label_x']
                output['axis_label_x'] = output['axis_label_y']
                output['axis_label_y'] = temp
            else:
                data_no_id = sort_mult_tuples(data_no_id, 0)
                output['groups'] = [x[0] for x in data_no_id]
                output['values'] = [x[1] for x in data_no_id]
            group_types = set(output['groups'])
            colors = []
            for i in group_types:
                colors.append(output['groups'].count(i)/len(output['groups'])) 
            

    else:
        output['datatype'] = None
    return output

#Takes a list of multinomial variables and if they are all numeric, it sorts the list.
def sort_mult_list(mult):
    num_mult = []
    for i in mult:
        try:
            num_mult.append(int(float(i)))
        except ValueError:
            return mult
    return sorted(num_mult)

#Takes a list of tuples and if the all the elements at index ind are numeric,
#it returns a list of tuples sorted by the value at ind, which has been converted to an int.
def sort_mult_tuples(mult, ind):

    def sort_func(tup):
        return float(tup[ind])

    num_mult = []    
    for i in mult:
        try:
            i_l = list(i)
            i_l[ind] = int(float(i[ind]))
            num_mult.append(tuple(i_l)) 
        except ValueError:
            return mult

    return sorted(num_mult, key = sort_func)

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

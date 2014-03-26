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
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import MaxNLocator
import matplotlib.gridspec as gs
import matplotlib.cm
import pandas as pd
import numpy
import utils
import functions
import data_utils as du
import math

def turn_off_labels(subplot):
    subplot.axes.get_xaxis().set_visible(False)
    subplot.axes.get_yaxis().set_visible(False)
         

def plot_general_histogram(colnames, data, M_c, filename=None, scatter=False, pairwise=False):
    '''
    colnames: list of column names
    data: list of tuples (first list is a list of rows, so each inner tuples is a row)
    colnames = ['name', 'age'], data = [('bob',37), ('joe', 39),...]
    scatter: False if histogram, True if scatterplot
    '''
    if pairwise:
        gsp = gs.GridSpec(1, 1)#temp values for now.
        plots = create_pairwise_plot(colnames, data, M_c, gsp)
    else:
        f, ax = p.subplots()
        create_plot(parse_data_for_hist(colnames, data, M_c), ax, horizontal=True)
    if filename:
        p.savefig(filename)
        p.close()
    else:
        p.show()

def create_plot(parsed_data, subplot, label_x=True, label_y=True, text=None, compress=False, **kwargs):
    """
    Takes parsed data and a subplot object, and creates a plot of the data on that subplot object.
    """
    if parsed_data['datatype'] == 'mult1D':
        if len(parsed_data['data']) == 0:
            return
        if 'horizontal' in kwargs and kwargs['horizontal']:
            subplot.tick_params(top='off', bottom='off', left='off', right='off')
            subplot.axes.get_yaxis().set_ticks([])
            labels = parsed_data['labels']
            datapoints = parsed_data['data']
            num_vals = len(labels)
            ind = np.arange(num_vals)
            width = .5
            subplot.barh(ind, datapoints, width, color=matplotlib.cm.Blues(0.5), align='center')
            subplot.axes.get_yaxis().set_ticks(range(len(labels)))
            subplot.axes.get_yaxis().set_ticklabels(labels)
            subplot.set_ylabel(parsed_data['axis_label'])
            if compress:
                subplot.axes.get_xaxis().set_visible(False)            
        else:
            subplot.tick_params(top='off', bottom='off', left='off', right='off')
            subplot.axes.get_xaxis().set_ticks([])
            labels = parsed_data['labels']
            datapoints = parsed_data['data']
            num_vals = len(labels)
            ind = np.arange(num_vals)
            width = .5
            subplot.bar(ind, datapoints, width, color=matplotlib.cm.Blues(0.5), align='center')
            subplot.axes.get_xaxis().set_ticks(range(len(labels)))
            subplot.axes.get_xaxis().set_ticklabels(labels)
            subplot.set_xlabel(parsed_data['axis_label'])
            if compress:
                subplot.axes.get_yaxis().set_visible(False)
        
    elif parsed_data['datatype'] == 'cont1D':
        if len(parsed_data['data']) == 0:
            return
        datapoints = parsed_data['data']
        subplot.series = pd.Series(datapoints)
        if 'horizontal' in kwargs and kwargs['horizontal']:
            subplot.series.hist(normed=True, color=matplotlib.cm.Blues(0.5), orientation='horizontal')
            subplot.set_ylabel(parsed_data['axis_label'])
            if compress:
                subplot.axes.get_xaxis().set_visible(False)
                subplot.axes.get_yaxis().set_major_locator(MaxNLocator(nbins = 3))                
        else:
            subplot.series.hist(normed=True, color=matplotlib.cm.Blues(0.5))
            subplot.set_xlabel(parsed_data['axis_label'])
            if compress:
                subplot.axes.get_xaxis().set_major_locator(MaxNLocator(nbins = 3))
                subplot.axes.get_yaxis().set_visible(False)
            else:
                subplot.series.dropna().plot(kind='kde', style='r--')                 

    elif parsed_data['datatype'] == 'contcont':
        if len(parsed_data['data_y']) == 0 or len(parsed_data['data_x']) == 0:
            return
        subplot.hist2d(parsed_data['data_y'], parsed_data['data_x'], bins=max(len(parsed_data['data_x'])/200,40), norm=LogNorm(), cmap=matplotlib.cm.Blues)
        if not compress:
            subplot.set_xlabel(parsed_data['axis_label_x'])
            subplot.set_ylabel(parsed_data['axis_label_y'])
        else:
            turn_off_labels(subplot)
        
    elif parsed_data['datatype'] == 'multmult':
        if len(parsed_data['data']) == 0:
            return
        subplot.tick_params(labelcolor='b', top='off', bottom='off', left='off', right='off')
        subplot.axes.get_xaxis().set_ticks([])
        unique_xs = parsed_data['labels_x']
        unique_ys = parsed_data['labels_y']
        dat = parsed_data['data']
        norm_a = Normalize(vmin=dat.min(), vmax=dat.max()) 
        subplot.imshow(parsed_data['data'],norm=Normalize(), interpolation='nearest',  cmap=matplotlib.cm.Blues, aspect = float(len(unique_xs))/len(unique_ys))

        subplot.axes.get_xaxis().set_ticks(range(len(unique_xs)))
        subplot.axes.get_xaxis().set_ticklabels(unique_xs)
        subplot.axes.get_yaxis().set_ticks(range(len(unique_ys)))
        subplot.axes.get_yaxis().set_ticklabels(unique_ys)
        if not compress:
            subplot.set_xlabel(parsed_data['axis_label_x'])
            subplot.set_ylabel(parsed_data['axis_label_y'])
        else:
            turn_off_labels(subplot)


    elif parsed_data['datatype'] == 'multcont':
        # Multinomial is always first. parsed_data['transpose'] is true if multinomial should be on Y axis.
        values = parsed_data['values']
        groups = parsed_data['groups']
        vert = not parsed_data['transpose']
        subplot.boxplot(values, vert=vert)
       

        if compress:
            turn_off_labels(subplot)
        else:
            if vert:
                xtickNames = p.setp(subplot, xticklabels=groups)
                p.setp(xtickNames, rotation=90, fontsize=8)
            else:
                p.setp(subplot, yticklabels=groups)

    else:
        raise Exception('Unexpected data type, or too many arguments')

    x0,x1 = subplot.get_xlim()
    y0,y1 = subplot.get_ylim()
    aspect = (abs(float((x1-x0)))/abs(float((y1-y0))))
    subplot.set_aspect(aspect)

    return subplot

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
    data_no_id = [] # This will be the data with the row_ids removed if present
    if colnames[0] == 'row_id':
        columns.pop(0)
    if len(data_c) == 0:
        raise utils.BayesDBError('There are no datapoints that contain values from every category specified. Try excluding columns with many NaN values.')
    if len(columns) == 1:
        if colnames[0] == 'row_id':
            data_no_id = [x[1] for x in data_c]
        else:
            data_no_id = [x[0] for x in data_c]
        output['axis_label'] = columns[0]
        output['title'] = columns[0]

        # Allow col_idx to be None, to allow for predictive functions to be plotted.
        if columns[0] in M_c['name_to_idx']:
            col_idx = M_c['name_to_idx'][columns[0]]
        else:
            col_idx = None

        # Treat not-column (e.g. function) the same as continuous, since no code to value conversion.            
        if col_idx is None or M_c['column_metadata'][col_idx]['modeltype'] == 'normal_inverse_gamma':
            output['datatype'] = 'cont1D'
            output['data'] = np.array(data_no_id)
            
        elif M_c['column_metadata'][col_idx]['modeltype'] == 'symmetric_dirichlet_discrete':
            unique_labels = sorted(sort_mult_list(M_c['column_metadata'][M_c['name_to_idx'][columns[0]]]['code_to_value'].keys()))
            np_data = np.array(data_no_id)
            counts = []
            for label in unique_labels:
                counts.append(sum(np_data==str(label)))
            output['datatype'] = 'mult1D'
            output['labels'] = unique_labels
            output['data'] = counts

    elif len(columns) == 2:
        if colnames[0] == 'row_id':
            data_no_id = [(x[1], x[2]) for x in data_c]
        else:
            data_no_id = [(x[0], x[1]) for x in data_c]

        types = []

        # Treat not-column (e.g. function) the same as continuous, since no code to value conversion.
        if columns[0] in M_c['name_to_idx']:
            col_idx_1 = M_c['name_to_idx'][columns[0]]
            types.append(M_c['column_metadata'][col_idx_1]['modeltype'])
        else:
            col_idx_1 = None
            types.append('normal_inverse_gamma')
        if columns[1] in M_c['name_to_idx']:
            col_idx_2 = M_c['name_to_idx'][columns[1]]
            types.append(M_c['column_metadata'][col_idx_2]['modeltype'])            
        else:
            col_idx_2 = None
            types.append('normal_inverse_gamma')            
        types = tuple(types)
        
        output['axis_label_x'] = columns[1]
        output['axis_label_y'] = columns[0]
        output['title'] = columns[0] + ' -versus- ' + columns[1]
 
        if types[0] == 'normal_inverse_gamma' and types[1] == 'normal_inverse_gamma':
            output['datatype'] = 'contcont'
            output['data_x'] = [x[0] for x in data_no_id]
            output['data_y'] = [x[1] for x in data_no_id]

        elif types[0] == 'symmetric_dirichlet_discrete' and types[1] == 'symmetric_dirichlet_discrete':
            counts = {}
            for i in data_no_id:
                if i in counts:
                    counts[i]+=1
                else:
                    counts[i]=1
            unique_xs = sort_mult_list(list(M_c['column_metadata'][col_idx_2]['code_to_value'].keys()))
            unique_ys = sort_mult_list(list(M_c['column_metadata'][col_idx_1]['code_to_value'].keys()))
            unique_ys.reverse()#Hack to reverse the y's
            counts_array = numpy.zeros(shape=(len(unique_ys), len(unique_xs)))
            for i in counts:
                counts_array[len(unique_ys) - 1 - M_c['column_metadata'][col_idx_1]['code_to_value'][i[0]]] [M_c['column_metadata'][col_idx_2]['code_to_value'][i[1]]] = float(counts[i])#hack to reverse ys
            output['datatype'] = 'multmult'
            output['data'] = counts_array
            output['labels_x'] = unique_xs
            output['labels_y'] = unique_ys

        elif 'normal_inverse_gamma' in types and 'symmetric_dirichlet_discrete' in types:
            output['datatype'] = 'multcont'
            beans = {}
            #TODO combine these cases with a variable to set the thigns that are different.
            if types[0] == 'normal_inverse_gamma':                
                groups = sorted(sort_mult_list(M_c['column_metadata'][M_c['name_to_idx'][columns[1]]]['code_to_value'].keys()))
                for i in groups:
                    beans[i] = []
                data_no_id = sort_mult_tuples(data_no_id, 1)
                for i in data_no_id:
                        beans[i[1]].append(i[0])

                output['groups'] = groups
                output['values'] = [beans[x] for x in groups]
                output['transpose'] = False
            else:
                groups = sort_mult_list(M_c['column_metadata'][M_c['name_to_idx'][columns[0]]]['code_to_value'].keys())
                for i in groups:
                    beans[i] = []
                data_no_id = sort_mult_tuples(data_no_id, 0)
                for i in data_no_id:
                    beans[i[0]].append(i[1])

                output['groups'] = groups
                output['values'] = [beans[x] for x in groups]
                output['transpose'] = True

            group_types = set(output['groups'])
    else:
        output['datatype'] = None
    return output

def create_pairwise_plot(colnames, data, M_c, gsp):
    output = {}
    columns = colnames[:]
    data_no_id = [] #This will be the data with the row_ids removed if present
    if colnames[0] == 'row_id':
        columns.pop(0)
        data_no_id = [x[1:] for x in data]
    else:
        data_no_id = data[:]

    gsp = gs.GridSpec(len(columns), len(columns))
    for i in range(len(columns)):
        for j in range(len(columns)):
            if j == 0 and i < len(columns) - 1:
                #left hand marginals
                sub_colnames = [columns[i]]
                sub_data = [[x[i]] for x in data_no_id]
                data = parse_data_for_hist(sub_colnames, sub_data, M_c)
                create_plot(data, p.subplot(gsp[i, j], adjustable='box', aspect=1), False, False, columns[i], horizontal=True, compress=True)
                
            elif i == len(columns) - 1 and j > 0:
                #bottom marginals
                subdata = None
                if j == 1:
                    sub_colnames = [columns[len(columns)-1]]
                    sub_data = [[x[len(columns) - 1]] for x in data_no_id]
                else:
                    sub_colnames = [columns[j-2]]
                    sub_data = [[x[j-2]] for x in data_no_id]
                data = parse_data_for_hist(sub_colnames, sub_data, M_c)
                create_plot(data, p.subplot(gsp[i, j], adjustable='box', aspect=1), False, False, columns[j-2], horizontal=False, compress=True)

            elif (j != 0 and i != len(columns)-1) and j < i+2:
                
                j_col = j-2
                if j == 1:
                    j_col = len(columns) - 1
                sub_colnames = [columns[i], columns[j_col]]
                sub_data = [[x[i], x[j_col]] for x in data_no_id]
                data = parse_data_for_hist(sub_colnames, sub_data, M_c)
                create_plot(data, p.subplot(gsp[i, j]), False, False, horizontal=True, compress=True)
            else:
                pass


#Takes a list of multinomial variables and if they are all numeric, it sorts the list.
def sort_mult_list(mult):
    #testing this
    return mult
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

    #testing this next line
    return mult

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
    fig = p.figure()
    fig.set_size_inches(16, 12)
    p.imshow(matrix, interpolation='none',
                 cmap=matplotlib.cm.Blues, vmin=0, vmax=1)
    p.colorbar()
    p.gca().set_yticks(range(len(column_names)))
    p.gca().set_yticklabels(column_names, size='small')
    p.gca().set_xticks(range(len(column_names)))
    p.gca().set_xticklabels(column_names, rotation=90, size='small')
    p.title(title)
    if filename:
        p.savefig(filename)
    else:
        fig.show()



def _create_histogram(M_c, data, columns, mc_col_indices, filename):
  dir=S.path.web_resources_data_dir
  full_filename = os.path.join(dir, filename)
  num_rows = data.shape[0]
  num_cols = data.shape[1]
  #
  p.figure()
  # col_i goes from 0 to number of predicted columns
  # mc_col_idx is the original column's index in M_c
  for col_i in range(num_cols):
    mc_col_idx = mc_col_indices[col_i]
    data_i = data[:, col_i]
    ax = p.subplot(1, num_cols, col_i, title=columns[col_i])
    if M_c['column_metadata'][mc_col_idx]['modeltype'] == 'normal_inverse_gamma':
      p.hist(data_i, orientation='horizontal')
    else:
      str_data = [du.convert_code_to_value(M_c, mc_col_idx, code) for code in data_i]
      unique_labels = list(set(str_data))
      np_str_data = np.array(str_data)
      counts = []
      for label in unique_labels:
        counts.append(sum(np_str_data==label))
      num_vals = len(M_c['column_metadata'][mc_col_idx]['code_to_value'])
      rects = p.barh(range(num_vals), counts)
      heights = np.array([rect.get_height() for rect in rects])
      ax.set_yticks(np.arange(num_vals) + heights/2)
      ax.set_yticklabels(unique_labels)
  p.tight_layout()
  p.savefig(full_filename)

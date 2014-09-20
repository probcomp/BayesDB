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
import pandas
import numpy
import utils
import functions
import data_utils as du
import math

def turn_off_labels(subplot):
    subplot.axes.get_xaxis().set_visible(False)
    subplot.axes.get_yaxis().set_visible(False)


def plot_general_histogram(colnames, data, M_c, schema_full, filename=None, scatter=False,
                           remove_key=False):
    '''
    colnames: list of column names
    data: list of tuples (first list is a list of rows, so each inner tuples is a row)
    colnames = ['name', 'age'], data = [('bob',37), ('joe', 39),...]
    scatter: False if histogram, True if scatterplot
    '''
    numcols = len(colnames)
    if remove_key:
        numcols -= 1

    if numcols > 1:
        gsp = gs.GridSpec(1, 1)
        plots = create_pairwise_plot(colnames, data, M_c, schema_full, gsp, remove_key=remove_key)
    else:
        f, ax = p.subplots()
        parsed_data = parse_data_for_hist(colnames, data, M_c, schema_full, remove_key=remove_key)
        create_plot(parsed_data, ax, horizontal=True)

    if filename:
        p.savefig(filename)
        p.close()
    else:
        p.show()


def create_plot(parsed_data, subplot, label_x=True, label_y=True, text=None, compress=False,
                super_compress=False, **kwargs):
    """
    Takes parsed data and a subplot object, and creates a plot of the data on that subplot object.
    """
    if parsed_data['datatype'] == 'mult1D':
        if len(parsed_data['data']) == 0:
            return
        subplot.tick_params(top='off', bottom='off', left='off', right='off')
        subplot.axes.get_yaxis().set_ticks([])
        labels = parsed_data['labels']
        datapoints = parsed_data['data']
        num_vals = len(labels)
        ind = np.arange(num_vals)
        width = 0.5

        horizontal = 'horizontal' in kwargs and kwargs['horizontal']
        rot = (horizontal != super_compress)

        if horizontal:
            plot_method = subplot.barh
            label_method = subplot.set_ylabel
            tick_axis = subplot.axes.get_yaxis()
            hide_axis = subplot.axes.get_xaxis()
        else:
            plot_method = subplot.bar
            label_method = subplot.set_xlabel
            tick_axis = subplot.axes.get_xaxis()
            hide_axis = subplot.axes.get_yaxis()

        plot_method(ind, datapoints, width, color=matplotlib.cm.Blues(0.5), align='center')
        label_method(parsed_data['axis_label'])

        n_labels = len(labels)

        if (not compress and len(labels) < 15) or (compress and len(labels) < 5):
            tick_axis.set_ticks(range(n_labels))
            tick_axis.set_ticklabels(labels)
        if compress:
            hide_axis.set_visible(False)

    elif parsed_data['datatype'] == 'cont1D':
        if len(parsed_data['data']) == 0:
            return
        datapoints = parsed_data['data']
        subplot.series = pandas.Series(datapoints)
        horizontal = 'horizontal' in kwargs and kwargs['horizontal']

        if horizontal:
            subplot.series.hist(normed=True, color=matplotlib.cm.Blues(0.5),
                                orientation='horizontal')
            label_method = subplot.set_ylabel
            hide_axis = subplot.axes.get_xaxis()
            major_axis = subplot.axes.get_yaxis()
        else:
            subplot.series.hist(normed=True, color=matplotlib.cm.Blues(0.5))
            label_method = subplot.set_xlabel
            hide_axis = subplot.axes.get_yaxis()
            major_axis = subplot.axes.get_xaxis()
            if not compress:
                subplot.series.dropna().plot(kind='kde', style='r--')

        label_method(parsed_data['axis_label'])

        if compress:
            hide_axis.set_visible(False)
            major_axis.set_major_locator(MaxNLocator(nbins=3))

    elif parsed_data['datatype'] == 'contcont':
        if len(parsed_data['data_y']) == 0 or len(parsed_data['data_x']) == 0:
            return
        subplot.hist2d(parsed_data['data_y'], parsed_data['data_x'],
                       bins=max(len(parsed_data['data_x'])/200, 40),
                       norm=LogNorm(), cmap=matplotlib.cm.Blues)
        if not compress:
            subplot.set_xlabel(parsed_data['axis_label_x'])
            subplot.set_ylabel(parsed_data['axis_label_y'])
        else:
            turn_off_labels(subplot)

    elif parsed_data['datatype'] == 'multmult':
        if len(parsed_data['data']) == 0:
            return
        subplot.tick_params(labelcolor='b', top='off', bottom='off', left='off', right='off')
        # subplot.axes.get_xaxis().set_ticks([])
        unique_xs = parsed_data['labels_x']
        unique_ys = parsed_data['labels_y']
        dat = parsed_data['data']
        norm_a = Normalize(vmin=dat.min(), vmax=dat.max())
        subplot.imshow(parsed_data['data'], norm=Normalize(), interpolation='nearest',
                       cmap=matplotlib.cm.Blues, aspect=float(len(unique_xs))/len(unique_ys))

        subplot.axes.get_xaxis().set_ticks(range(len(unique_xs)))
        subplot.axes.get_xaxis().set_ticklabels(unique_xs, rotation=90)
        subplot.axes.get_yaxis().set_ticks(range(len(unique_ys)))
        subplot.axes.get_yaxis().set_ticklabels(unique_ys)
        if not compress:
            subplot.set_xlabel(parsed_data['axis_label_x'])
            subplot.set_ylabel(parsed_data['axis_label_y'])
        else:
            turn_off_labels(subplot)

    elif parsed_data['datatype'] == 'multcont':
        # categorical is always first. parsed_data['transpose'] is true if categorical should be on
        # Y axis.
        values = parsed_data['values']
        groups = parsed_data['groups']
        vert = not parsed_data['transpose']
        subplot.boxplot(values, vert=vert)

        if compress:
            turn_off_labels(subplot)
        else:
            if vert:
                xtickNames = p.setp(subplot, xticklabels=groups)
                p.setp(xtickNames, fontsize=8, rotation=90)
            else:
                p.setp(subplot, yticklabels=groups)

    else:
        raise Exception('Unexpected data type, or too many arguments')

    x0, x1 = subplot.get_xlim()
    y0, y1 = subplot.get_ylim()
    aspect = (abs(float((x1 - x0))) / abs(float((y1 - y0))))
    subplot.set_aspect(aspect)
    return subplot


def any_nan(row):
    return any([isinstance(x, float) and math.isnan(x) for x in row])


def parse_data_for_hist(colnames, data, M_c, schema_full, remove_key=False):
    columns = colnames[:]
    # Remove key column if present
    if remove_key:
        columns.pop(0)
        data = [row[1:] for row in data]
    # Remove any rows with nan values.
    data = [row for row in data if not any_nan(row)]
    # Stop if there are no rows remaining after cleaning missing values.
    if len(data) == 0:
        raise utils.BayesDBError('There are no datapoints that contain values from every category '
                                 'specified. Try excluding columns with many NaN values.')

    # Pull items from M_c to simplify code throughout the rest of this function
    name_to_idx = M_c['name_to_idx']
    column_metadata = M_c['column_metadata']
    cctypes = [schema_full[column] for column in columns]

    # Treat cyclic as numerical until we establish what we want in a cyclic plot.
    for cctype_idx, cctype in enumerate(cctypes):
        if cctype == 'cyclic':
            cctypes[cctype_idx] = 'numerical'

    output = {}
    if len(columns) == 1:
        np_data = np.array([x[0] for x in data])

        # Allow col_idx to be None, to allow for predictive functions to be plotted.
        if columns[0] in name_to_idx:
            col_idx = name_to_idx[columns[0]]
        else:
            col_idx = None

        # Treat not-column (e.g. function) the same as numerical, since no code to value conversion.
        if col_idx is None or cctypes[0] == 'numerical':
            output['datatype'] = 'cont1D'
            output['data'] = np_data
        elif cctypes[0] == 'categorical':
            unique_labels = sorted(column_metadata[name_to_idx[columns[0]]]['code_to_value'].keys())
            counts = []
            for label in unique_labels:
                counts.append(sum(np_data == str(label)))
            output['datatype'] = 'mult1D'
            output['labels'] = unique_labels
            output['data'] = counts

        try:
            # try to get short names from M_c_full
            short_name = M_c['column_codebook'][col_idx]['short_name']
            output['axis_label'] = short_name
            output['title'] = short_name
        except KeyError:
            output['axis_label'] = columns[0]
            output['title'] = columns[0]

    elif len(columns) == 2:
        # Treat not-column (e.g. function) the same as numerical, since no code to value conversion.
        if columns[0] in name_to_idx:
            col_idx_1 = name_to_idx[columns[0]]
        else:
            col_idx_1 = None
        if columns[1] in name_to_idx:
            col_idx_2 = name_to_idx[columns[1]]
        else:
            col_idx_2 = None

        if cctypes[0] == 'numerical' and cctypes[1] == 'numerical':
            output['datatype'] = 'contcont'
            output['data_x'] = [x[0] for x in data]
            output['data_y'] = [x[1] for x in data]

        elif cctypes[0] == 'categorical' and cctypes[1] == 'categorical':
            counts = {}  # keys are (var 1 value, var 2 value)
            # data contains a tuple for each datapoint: (value of var 1, value of var 2)
            for row in data:
                row = tuple(row)
                if row in counts:
                    counts[row] += 1
                else:
                    counts[row] = 1

            # these are the values.
            unique_xs = sorted(column_metadata[col_idx_2]['code_to_value'].keys())
            unique_ys = sorted(column_metadata[col_idx_1]['code_to_value'].keys())
            unique_ys.reverse()  # Hack to reverse the y's
            x_ordered_codes = [du.convert_value_to_code(M_c, col_idx_2, xval) for xval in unique_xs]
            y_ordered_codes = [du.convert_value_to_code(M_c, col_idx_1, yval) for yval in unique_ys]

            # Make count array: indexed by y index, x index
            counts_array = numpy.zeros(shape=(len(unique_ys), len(unique_xs)))
            for i in counts:
                # this converts from value to code
                y_index = y_ordered_codes.index(column_metadata[col_idx_1]['code_to_value'][i[0]])
                x_index = x_ordered_codes.index(column_metadata[col_idx_2]['code_to_value'][i[1]])
                counts_array[y_index][x_index] = float(counts[i])
            output['datatype'] = 'multmult'
            output['data'] = counts_array
            output['labels_x'] = unique_xs
            output['labels_y'] = unique_ys

        elif 'numerical' in cctypes and 'categorical' in cctypes:
            output['datatype'] = 'multcont'
            categories = {}

            categorical_column = cctypes.index('categorical')

            groups = sorted(column_metadata[name_to_idx[columns[categorical_column]]]['code_to_value'].keys())
            for i in groups:
                categories[i] = []
            for i in data:
                categories[i[categorical_column]].append(i[1 - categorical_column])

            output['groups'] = groups
            output['values'] = [categories[x] for x in groups]
            output['transpose'] = (categorical_column == 0)

        try:
            # try to get short names from M_c_full
            columns[0] = M_c['column_codebook'][col_idx_1]['short_name']
            columns[1] = M_c['column_codebook'][col_idx_2]['short_name']
        except KeyError:
            pass

        output['axis_label_x'] = columns[1]
        output['axis_label_y'] = columns[0]

        output['title'] = columns[0] + ' -versus- ' + columns[1]

    else:
        output['datatype'] = None

    return output


def create_pairwise_plot(colnames, data, M_c, schema_full, gsp, remove_key=False):
    columns = colnames[:]
    # Remove key column if present
    if remove_key:
        columns.pop(0)
        data = [row[1:] for row in data]
    # Remove any rows with nan values.
    data = [row for row in data if not any_nan(row)]
    # Stop if there are no rows remaining after cleaning missing values.
    if len(data) == 0:
        raise utils.BayesDBError('There are no datapoints that contain values from every category '
                                 'specified. Try excluding columns with many NaN values.')

    output = {}

    n_columns = len(columns)
    # Rotate outer labels if there are more than 6 columns to be plotted.
    super_compress = n_columns > 6
    gsp = gs.GridSpec(n_columns, n_columns)
    for i in range(n_columns):
        for j in range(n_columns):
            if j == 0 and i < n_columns - 1:
                # left hand marginals
                sub_colnames = [columns[i]]
                sub_data = [[x[i]] for x in data]
                parsed_data = parse_data_for_hist(sub_colnames, sub_data, M_c, schema_full)
                create_plot(parsed_data, p.subplot(gsp[i, j], adjustable='box', aspect=1), False,
                            False, columns[i], horizontal=True, compress=True,
                            super_compress=super_compress)

            elif i == n_columns - 1 and j > 0:
                # bottom marginals
                subdata = None
                if j == 1:
                    sub_colnames = [columns[n_columns - 1]]
                    sub_data = [[x[n_columns - 1]] for x in data]
                else:
                    sub_colnames = [columns[j - 2]]
                    sub_data = [[x[j - 2]] for x in data]
                parsed_data = parse_data_for_hist(sub_colnames, sub_data, M_c, schema_full)
                create_plot(parsed_data, p.subplot(gsp[i, j], adjustable='box', aspect=1), False,
                            False, columns[j-2], horizontal=False, compress=True,
                            super_compress=super_compress)

            elif (j != 0 and i != n_columns - 1) and j < i + 2:
                # pairwise joints
                j_col = j - 2
                if j == 1:
                    j_col = n_columns - 1
                sub_colnames = [columns[i], columns[j_col]]
                sub_data = [[x[i], x[j_col]] for x in data]
                parsed_data = parse_data_for_hist(sub_colnames, sub_data, M_c, schema_full)
                create_plot(parsed_data, p.subplot(gsp[i, j]), False, False, horizontal=True,
                            compress=True, super_compress=super_compress)
            else:
                pass


def plot_matrix(matrix, column_names, title='', filename=None):
    # actually create figure
    fig = p.figure()
    fig.set_size_inches(16, 12)
    p.imshow(matrix, interpolation='none', cmap=matplotlib.cm.Blues, vmin=0, vmax=1)
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
    dir = S.path.web_resources_data_dir
    full_filename = os.path.join(dir, filename)
    num_rows = data.shape[0]
    num_cols = data.shape[1]

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
                counts.append(sum(np_str_data == label))
            num_vals = len(M_c['column_metadata'][mc_col_idx]['code_to_value'])
            rects = p.barh(range(num_vals), counts)
            heights = np.array([rect.get_height() for rect in rects])
            ax.set_yticks(np.arange(num_vals) + heights/2)
            ax.set_yticklabels(unique_labels)

    p.tight_layout()
    p.savefig(full_filename)

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

import os
import math
import json
import requests
import prettytable
import pandas
import numpy as np

import pylab
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import MaxNLocator
import matplotlib.gridspec as gs
import matplotlib.cm

import pdb

default_args = {
    'pretty': True,  # pretty print tables
    'timing': False,
    'wait': False,
    'plots': None,
    'yes': True,
    'debug': False,
    'pandas_df': None,
    'pandas_output': True,
    'key_column': 0
}   # make sure that a new column for ID's are set by default


####################################################################################################
#                                           BEGIN COPIED CODE
####################################################################################################
# Copy-paste helper functions (docstrings removed)
# From utils:
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


# From data_utils:
def construct_pandas_df(query_obj):
    if len(query_obj['data']) == 0:
        data = None
    else:
        data = [list(row) for row in query_obj['data']]
    pandas_df = pandas.DataFrame(data=data, columns=query_obj['columns'])
    return pandas_df


def convert_code_to_value(M_c, cidx, code):
    if np.isnan(code) or code == 'nan':
        return code
    elif M_c['column_metadata'][cidx]['modeltype'] in ['normal_inverse_gamma', 'vonmises']:
        return float(code)
    else:
        try:
            return M_c['column_metadata'][cidx]['value_to_code'][int(code)]
        except KeyError:
            return M_c['column_metadata'][cidx]['value_to_code'][str(int(code))]


def convert_value_to_code(M_c, cidx, value):
    if M_c['column_metadata'][cidx]['modeltype'] in ['normal_inverse_gamma', 'vonmises']:
        return float(value)
    else:
        try:
            return M_c['column_metadata'][cidx]['code_to_value'][str(value)]
        except KeyError:
            raise Exception("Error: value '%s' not in btable." % str(value))


# From plotting_utils (pretty much all of plotting utils)
def turn_off_labels(subplot):
    subplot.axes.get_xaxis().set_visible(False)
    subplot.axes.get_yaxis().set_visible(False)


def plot_general_histogram(colnames, data, M_c, filename=None, scatter=False, remove_key=False):
    numcols = len(colnames)
    if remove_key:
        numcols -= 1
    if numcols > 1:
        gsp = gs.GridSpec(1, 1)
        create_pairwise_plot(colnames, data, M_c, gsp, remove_key=remove_key)
    else:
        f, ax = pylab.subplots()
        create_plot(parse_data_for_hist(colnames, data, M_c, remove_key=remove_key), ax,
                    horizontal=True)
    if filename:
        pylab.savefig(filename)
        pylab.close()
    else:
        pylab.show()


def parse_data_for_hist(colnames, data, M_c, remove_key=False):
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
    data_no_id = []  # This will be the data with the row_ids removed if present
    if remove_key:
        columns.pop(0)
    if len(data_c) == 0:
        raise Exception('There are no datapoints that contain values from every category specified.'
                        ' Try excluding columns with many NaN values.')
    if len(columns) == 1:
        if remove_key:
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

        # Treat not-column (e.g. function) the same as continuous, since no code to value conversion
        if col_idx is None or M_c['column_metadata'][col_idx]['modeltype'] == 'normal_inverse_gamma':
            output['datatype'] = 'cont1D'
            output['data'] = np.array(data_no_id)

        elif M_c['column_metadata'][col_idx]['modeltype'] == 'symmetric_dirichlet_discrete':
            unique_labels = sorted(M_c['column_metadata'][M_c['name_to_idx'][columns[0]]]['code_to_value'].keys())
            np_data = np.array(data_no_id)
            counts = []
            for label in unique_labels:
                counts.append(sum(np_data == str(label)))
            output['datatype'] = 'mult1D'
            output['labels'] = unique_labels
            output['data'] = counts

    elif len(columns) == 2:
        if remove_key:
            data_no_id = [(x[1], x[2]) for x in data_c]
        else:
            data_no_id = [(x[0], x[1]) for x in data_c]

        types = []

        # Treat not-column (e.g. function) the same as continuous, since no code to value conversion
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
            counts = {}  # keys are (var 1 value, var 2 value)
            # data_no_id is a tuple for each datapoint: (value of var 1, value of var 2)
            for i in data_no_id:
                if i in counts:
                    counts[i] += 1
                else:
                    counts[i] = 1

            # these are the values.
            unique_xs = sorted(M_c['column_metadata'][col_idx_2]['code_to_value'].keys())
            unique_ys = sorted(M_c['column_metadata'][col_idx_1]['code_to_value'].keys())
            unique_ys.reverse()  # Hack to reverse the y's
            x_ordered_codes = [convert_value_to_code(M_c, col_idx_2, xval) for xval in unique_xs]
            y_ordered_codes = [convert_value_to_code(M_c, col_idx_1, yval) for yval in unique_ys]

            # Make count array: indexed by y index, x index
            counts_array = np.zeros(shape=(len(unique_ys), len(unique_xs)))
            for i in counts:
                # this converts from value to code
                y_index = y_ordered_codes.index(M_c['column_metadata'][col_idx_1]['code_to_value'][i[0]])
                x_index = x_ordered_codes.index(M_c['column_metadata'][col_idx_2]['code_to_value'][i[1]])
                counts_array[y_index][x_index] = float(counts[i])
            output['datatype'] = 'multmult'
            output['data'] = counts_array
            output['labels_x'] = unique_xs
            output['labels_y'] = unique_ys

        elif 'normal_inverse_gamma' in types and 'symmetric_dirichlet_discrete' in types:
            output['datatype'] = 'multcont'
            categories = {}

            col = 0
            type = 1
            if types[0] == 'normal_inverse_gamma':
                type = 0
                col = 1

            groups = sorted(M_c['column_metadata'][M_c['name_to_idx'][columns[col]]]['code_to_value'].keys())
            for i in groups:
                categories[i] = []
            for i in data_no_id:
                categories[i[col]].append(i[type])

            output['groups'] = groups
            output['values'] = [categories[x] for x in groups]
            output['transpose'] = (type == 1)

    else:
        output['datatype'] = None
    return output


def create_plot(parsed_data, subplot, label_x=True, label_y=True, text=None, compress=False,
                super_compress=False, **kwargs):
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

            # rotate major label if super compress
            subplot.set_ylabel(parsed_data['axis_label'])

            if (not compress and len(labels) < 15) or (compress and len(labels) < 5):
                subplot.axes.get_yaxis().set_ticks(range(len(labels)))
                subplot.axes.get_yaxis().set_ticklabels(labels)
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

            # rotate major label if super compress
            subplot.set_xlabel(parsed_data['axis_label'])

            if (not compress and len(labels) < 15) or (compress and len(labels) < 5):
                subplot.axes.get_xaxis().set_ticks(range(len(labels)))
                subplot.axes.get_xaxis().set_ticklabels(labels, rotation=50)
            if compress:
                subplot.axes.get_yaxis().set_visible(False)

    elif parsed_data['datatype'] == 'cont1D':
        if len(parsed_data['data']) == 0:
            return
        datapoints = parsed_data['data']
        subplot.series = pandas.Series(datapoints)
        if 'horizontal' in kwargs and kwargs['horizontal']:
            subplot.series.hist(normed=True, color=matplotlib.cm.Blues(0.5),
                                orientation='horizontal')
            subplot.set_ylabel(parsed_data['axis_label'])
            if compress:
                subplot.axes.get_xaxis().set_visible(False)
                subplot.axes.get_yaxis().set_major_locator(MaxNLocator(nbins=3))
        else:
            subplot.series.hist(normed=True, color=matplotlib.cm.Blues(0.5))
            subplot.set_xlabel(parsed_data['axis_label'])
            if compress:
                subplot.axes.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
                subplot.axes.get_yaxis().set_visible(False)
            else:
                subplot.series.dropna().plot(kind='kde', style='r--')

    elif parsed_data['datatype'] == 'contcont':
        if len(parsed_data['data_y']) == 0 or len(parsed_data['data_x']) == 0:
            return
        subplot.hist2d(parsed_data['data_y'], parsed_data['data_x'],
                       bins=max(len(parsed_data['data_x'])/200, 40), norm=LogNorm(),
                       cmap=matplotlib.cm.Blues)
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
        values = parsed_data['values']
        groups = parsed_data['groups']
        vert = not parsed_data['transpose']
        subplot.boxplot(values, vert=vert)

        if compress:
            turn_off_labels(subplot)
        else:
            if vert:
                xtickNames = pylab.setp(subplot, xticklabels=groups)
                pylab.setp(xtickNames, fontsize=8, rotation=90)
            else:
                pylab.setp(subplot, yticklabels=groups)

    else:
        raise Exception('Unexpected data type, or too many arguments')

    x0, x1 = subplot.get_xlim()
    y0, y1 = subplot.get_ylim()
    aspect = (abs(float((x1-x0)))/abs(float((y1-y0))))
    subplot.set_aspect(aspect)
    return subplot


def create_pairwise_plot(colnames, data, M_c, gsp, remove_key=False):
    columns = colnames[:]
    data_no_id = []  # This will be the data with the row_ids removed if present
    if remove_key:
        columns.pop(0)
        data_no_id = [x[1:] for x in data]
    else:
        data_no_id = data[:]

    super_compress = len(columns) > 6  # rotate outer labels
    gsp = gs.GridSpec(len(columns), len(columns))
    for i in range(len(columns)):
        for j in range(len(columns)):
            if j == 0 and i < len(columns) - 1:
                # left hand marginals
                sub_colnames = [columns[i]]
                sub_data = [[x[i]] for x in data_no_id]
                data = parse_data_for_hist(sub_colnames, sub_data, M_c)
                create_plot(data, pylab.subplot(gsp[i, j], adjustable='box', aspect=1), False,
                            False, columns[i], horizontal=True, compress=True,
                            super_compress=super_compress)

            elif i == len(columns) - 1 and j > 0:
                # bottom marginals
                if j == 1:
                    sub_colnames = [columns[len(columns)-1]]
                    sub_data = [[x[len(columns) - 1]] for x in data_no_id]
                else:
                    sub_colnames = [columns[j-2]]
                    sub_data = [[x[j-2]] for x in data_no_id]
                data = parse_data_for_hist(sub_colnames, sub_data, M_c)
                create_plot(data, pylab.subplot(gsp[i, j], adjustable='box', aspect=1), False,
                            False, columns[j-2], horizontal=False, compress=True,
                            super_compress=super_compress)

            elif (j != 0 and i != len(columns)-1) and j < i+2:
                # pairwise joints
                j_col = j-2
                if j == 1:
                    j_col = len(columns) - 1
                sub_colnames = [columns[i], columns[j_col]]
                sub_data = [[x[i], x[j_col]] for x in data_no_id]
                data = parse_data_for_hist(sub_colnames, sub_data, M_c)
                create_plot(data, pylab.subplot(gsp[i, j]), False, False, horizontal=True,
                            compress=True, super_compress=super_compress)
            else:
                pass


def plot_matrix(matrix, column_names, title='', filename=None):
    # actually create figure
    fig = pylab.figure()
    fig.set_size_inches(16, 12)
    pylab.imshow(matrix, interpolation='none',
                 cmap=matplotlib.cm.Blues, vmin=0, vmax=1)
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
####################################################################################################
#                                           END COPIED CODE
####################################################################################################


class ClientRemote(object):
    """BayesDB remote client.

    Used to interface with an open BayesDB client through server_remote.py

    Example:
        Localhost example.
        To run the server: in a shell window:

        $ python server_remote.py
        Listening on port 8008...

        To interface with the server, from the python interactive shell:

        >>> from bayesdb.client_remote import ClientRemote
        >>> c = ClientRemote()
        NOTES:
        - Currently does not support interactive queries, thus all y/n prompts will be
        ignored. *Do not press return unless you mean it.*
        - The client will not notify you when asynchronous ANALYZE commands have completed.
        >>> c('SHOW MODELS FOR dha_demo', pretty=False) # do not pretty print tables
        {u'models': [[0, 501], [1, 501], [2, 501], [3, 501], [4, 501], [5, 501], [6, 501], [7, 501],
        [8, 501], [9, 501]]}
    """
    def __init__(self, bayesdb_host='127.0.0.1', bayesdb_port=8008):
        """Create a ClientRemote object.

        Args:
            bayesdb_host (str): The network address of the server. Default is '127.0.0.1'
            bayesdb_port (int): The server port. Default is 8008
        """
        self.hostname = bayesdb_host
        self.port = bayesdb_port
        self.URI = 'http://' + self.hostname + ':%d' % self.port
        self.call_id = 0
        print("NOTES:")
        print("- Currently does not support interactive queries, thus all y/n prompts will be\n"
              "ignored. *Do not press return unless you mean it.*")
        print("- The client will not notify you when asynchronous ANALYZE commands have completed.")

    def execute(self, bql_string, **kwargs):
        self.call_id += 1

        # construct arguments using defaults
        params = default_args
        params['call_input'] = bql_string
        for key, item in kwargs.iteritems():
            params[key] = item

        # get something for the user
        params['return_raw_result'] = True

        # ignore interactive queries
        # params['yes'] = True
        # params['pretty'] = False # so that we get output
        # params['pandas_output'] = False # cannot pass pandas object
        message = {
            'jsonrpc': '2.0',
            'method': 'execute',
            'params': params,
            'id': str(self.call_id),
            }
        json_message = json.dumps(message)

        self.call_id
        r = requests.put(self.URI, data=json_message)
        r.raise_for_status()
        out = json.loads(r.content)

        if isinstance(out, dict) and 'result' in out:
            if isinstance(out['result'][0], str) or isinstance(out['result'][0], unicode):
                print("ERROR: %s" % (out['result'][0]))
                return None

            result = out['result'][0]['result']
            method_name = out['result'][0]['method_name']
            client_dict = out['result'][0]['client_dict']
        else:
            if 'error' in out.keys():
                print(out['error']['message'])
            else:
                print(" Unexpected error in: call(client.execute, <%s>, %s)" % (params, self.URI))
            return None

        assert type(result) != int

        plots = params['plots']
        pretty = params['pretty']
        pandas_output = params['pandas_output']

        if plots is None:
            plots = 'DISPLAY' in os.environ.keys()

        if 'matrix' in result and (plots or client_dict['filename']):
            # Plot matrices
            plot_matrix(result['matrix'], result['column_names'], result['title'],
                        client_dict['filename'])
            if pretty:
                if 'column_lists' in result:
                    print(self.pretty_print(dict(column_lists=result['column_lists'])))
                return self.pretty_print(result)
            else:
                return result
        if ('plot' in client_dict and client_dict['plot']):
            if (plots or client_dict['filename']):
                # Plot generalized histograms or scatterplots
                plot_remove_key = method_name in ['select', 'infer']
                plot_general_histogram(result['columns'], result['data'], result['M_c'],
                                       client_dict['filename'], client_dict['scatter'],
                                       remove_key=plot_remove_key)
                return self.pretty_print(result)
            else:
                if 'message' not in result:
                    result['message'] = ""
                result['message'] = "Your query indicates that you would like to make a plot, but "\
                                    " in order to do so, you must either enable plotting in a "\
                                    "window or specify a filename to save to by appending 'SAVE TO"\
                                    " <filename>' to this command.\n" + result['message']

        if pretty:
            pp = self.pretty_print(result)
            print(pp)

        # Print warnings last so they're readable without scrolling backwards.
        if 'warnings' in result:
            """ Pretty-print warnings. """
            for warning in result['warnings']:
                print('WARNING: %s' % warning)

        if pandas_output and 'data' in result and 'columns' in result:
            result_pandas_df = construct_pandas_df(result)
            return result_pandas_df
        else:
            return result

    def __call__(self, bql_string, **kwargs):
        """Wrapper around execute."""
        return self.execute(bql_string, **kwargs)

    def pretty_print(self, query_obj):
        """
        Return a pretty string representing the output object.
        """
        assert type(query_obj) == dict
        result = ""
        if type(query_obj) == dict and 'message' in query_obj:
            result += query_obj["message"] + "\n"
        if 'data' in query_obj and 'columns' in query_obj:
            """ Pretty-print data table """
            pt = prettytable.PrettyTable()
            pt.field_names = query_obj['columns']
            for row in query_obj['data']:
                pt.add_row(row)
            result += str(pt)
        elif 'list' in query_obj:
            """ Pretty-print lists """
            result += str(query_obj['list'])
        elif 'column_names' in query_obj:
            """ Pretty-print cctypes """
            colnames = query_obj['column_names']
            zmatrix = query_obj['matrix']
            pt = prettytable.PrettyTable(hrules=prettytable.ALL, vrules=prettytable.ALL,
                                         header=False)
            pt.add_row([''] + list(colnames))
            for row, colname in zip(zmatrix, list(colnames)):
                pt.add_row([colname] + list(row))
            result += str(pt)
        elif 'columns' in query_obj:
            """ Pretty-print column list."""
            pt = prettytable.PrettyTable()
            pt.field_names = ['column']
            for column in query_obj['columns']:
                pt.add_row([column])
            result += str(pt)
        elif 'row_lists' in query_obj:
            """ Pretty-print multiple row lists, which are just names and row sizes. """
            pt = prettytable.PrettyTable()
            pt.field_names = ('Row List Name', 'Row Count')

            def get_row_list_sorting_key(x):
                """ To be used as the key function in a sort. Puts cc_2 ahead of cc_10, e.g. """
                name, count = x
                if '_' not in name:
                    return name
                s = name.split('_')
                end = s[-1]
                start = '_'.join(s[:-1])
                if is_int(end):
                    return (start, int(end))
                return name

            for name, count in sorted(query_obj['row_lists'], key=get_row_list_sorting_key):
                pt.add_row((name, count))
            result += str(pt)
        elif 'column_lists' in query_obj:
            """ Pretty-print multiple column lists. """
            print
            clists = query_obj['column_lists']
            for name, clist in clists:
                print("%s:" % name)
                pt = prettytable.PrettyTable()
                pt.field_names = clist
                print(pt)
        elif 'models' in query_obj:
            """ Pretty-print model info. """
            pt = prettytable.PrettyTable()
            pt.field_names = ('model_id', 'iterations')
            for (id, iterations) in query_obj['models']:
                pt.add_row((id, iterations))
            result += str(pt)

        if len(result) >= 1 and result[-1] == '\n':
            result = result[:-1]
        return result

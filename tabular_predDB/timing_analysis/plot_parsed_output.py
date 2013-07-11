import argparse
from collections import namedtuple
from collections import defaultdict
from collections import Counter
#
import pylab
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.plot_utils as pu


get_time_per_step = lambda timing_row: float(timing_row.time_per_step)
get_num_rows = lambda timing_row: timing_row.num_rows
get_num_cols = lambda timing_row: timing_row.num_cols
get_num_views = lambda timing_row: timing_row.num_views
get_num_clusters = lambda timing_row: timing_row.num_clusters
do_strip = lambda string: string.strip()
#
def parse_timing_file(filename):
    header, rows = du.read_csv(filename)
    _timing_row = namedtuple('timing_row', ' '.join(header))
    timing_rows = []
    for row in rows:
        row = map(do_strip, row)
        timing_row = _timing_row(*row)
        timing_rows.append(timing_row)
    return timing_rows

def group_results(timing_rows, get_fixed_parameters, get_variable_parameter):
    dict_of_dicts = defaultdict(dict)
    for timing_row in these_timing_rows:
        fixed_parameters = get_fixed_parameters(timing_row)
        variable_parameter = get_variable_parameter(timing_row)
        dict_of_dicts[fixed_parameters][variable_parameter] = timing_row
    return dict_of_dicts

num_cols_to_color = {'4':'b', '16':'r', '32':'m', '64':'g', '128':'c'}
num_rows_to_color = {'100':'b', '400':'r', '1000':'m', '4000':'y', '10000':'g'}
num_clusters_to_marker = {'10':'x', '20':'o', '50':'v'}
num_views_to_marker = {'1':'x', '2':'o', '4':'v'}
num_rows_to_marker = {'100':'x', '400':'o', '1000':'v', '4000':'1', '10000':'*'}
#
plot_parameter_lookup = dict(
    rows=dict(
        vary_what='rows',
        which_kernel='row_partition_assignments',
        get_fixed_parameters=lambda timing_row: 'Co=%s;Cl=%s;V=%s' % \
            (timing_row.num_cols, timing_row.num_clusters,
             timing_row.num_views),
        get_variable_parameter=get_num_rows,
        get_color_parameter=get_num_cols,
        color_dict=num_cols_to_color,
        get_marker_parameter=get_num_clusters,
        marker_dict=num_clusters_to_marker,
        ),
    cols=dict(
        vary_what='cols',
        which_kernel='column_partition_assignments',
        get_fixed_parameters=lambda timing_row: 'R=%s;Cl=%s;V=%s' % \
            (timing_row.num_rows, timing_row.num_clusters,
             timing_row.num_views),
        get_variable_parameter=get_num_cols,
        get_color_parameter=get_num_rows,
        color_dict=num_rows_to_color,
        get_marker_parameter=get_num_clusters,
        marker_dict=num_clusters_to_marker,
        ),
    clusters=dict(
        vary_what='clusters',
        which_kernel='row_partition_assignments',
        get_fixed_parameters=lambda timing_row: 'R=%s;Co=%s;V=%s' % \
            (timing_row.num_rows, timing_row.num_cols,
             timing_row.num_views),
        get_variable_parameter=get_num_clusters,
        get_color_parameter=get_num_rows,
        color_dict=num_rows_to_color,
        get_marker_parameter=get_num_views,
        marker_dict=num_views_to_marker,
        ),
    views=dict(
        vary_what='views',
        which_kernel='column_partition_assignments',
        get_fixed_parameters=lambda timing_row: 'R=%s;Co=%s;Cl=%s' % \
            (timing_row.num_rows, timing_row.num_cols,
             timing_row.num_clusters),
        get_variable_parameter=get_num_views,
        get_color_parameter=get_num_cols,
        color_dict=num_cols_to_color,
        get_marker_parameter=get_num_rows,
        marker_dict=num_rows_to_marker,
        ),
    )

import itertools
def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = itertools.cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = itertools.cycle(itertools.islice(nexts, pending))

get_first_label_value = lambda label: label[1+label.index('='):label.index(';')]
int_cmp = lambda x, y: cmp(int(x), int(y))
label_cmp = lambda x, y: cmp(int(get_first_label_value(x)), int(get_first_label_value(y)))
def plot_grouped_data(dict_of_dicts, plot_parameters, plot_filename=None):
    get_color_parameter = plot_parameters['get_color_parameter']
    color_dict = plot_parameters['color_dict']
    timing_row_to_color = lambda timing_row: \
        color_dict[get_color_parameter(timing_row)]
    get_marker_parameter = plot_parameters['get_marker_parameter']
    marker_dict = plot_parameters['marker_dict']
    timing_row_to_marker = lambda timing_row: \
        marker_dict[get_marker_parameter(timing_row)]
    vary_what = plot_parameters['vary_what']
    which_kernel = plot_parameters['which_kernel']
    #
    fh = pylab.figure()
    for configuration, run_data in dict_of_dicts.iteritems():
        x = sorted(run_data.keys())
        _y = [run_data[el] for el in x]
        y = map(get_time_per_step, _y)
        #
        plot_args = dict()
        first_timing_row = run_data.values()[0]
        color = timing_row_to_color(first_timing_row)
        plot_args['color'] = color
        marker = timing_row_to_marker(first_timing_row)
        plot_args['marker'] = marker
        label = str(configuration)
        plot_args['label'] = label
        #
        pylab.plot(x, y, **plot_args)
    #
    pylab.xlabel('# %s' % vary_what)
    pylab.ylabel('time per step (seconds)')
    pylab.title('Timing analysis for kernel: %s' % which_kernel)

    # fh = pu.legend_outside(bbox_to_anchor=(0.5, -.1), ncol=4, label_cmp=label_cmp)
    marker_handles = []
    marker_labels = []
    for label in sorted(marker_dict.keys(), cmp=int_cmp):
        marker = marker_dict[label]
        handle = pylab.Line2D([],[], color='k', marker=marker, linewidth=0)
        marker_handles.append(handle)
        marker_labels.append('#R='+label)

    color_handles = []
    color_labels = []
    for label in sorted(color_dict.keys(), cmp=int_cmp):
        color = color_dict[label]
        handle = pylab.Line2D([],[], color=color, linewidth=3)
        color_handles.append(handle)
        color_labels.append('#C='+label)

    # handles = pylab.append(marker_handles, color_handles)
    # labels = pylab.append(marker_labels, color_labels)
    num_marker_handles = len(marker_handles)
    num_color_handles = len(color_handles)
    num_to_add = abs(num_marker_handles - num_color_handles)
    if num_marker_handles < num_color_handles:
        add_to_handles = marker_handles
        add_to_labels = marker_labels
    else:
        add_to_handles = color_handles
        add_to_labels = color_labels
    for add_idx in range(num_to_add):
        add_to_handles.append(pylab.Line2D([],[], color=None, linewidth=0))
        add_to_labels.append('')
        
    handles = roundrobin(marker_handles, color_handles)
    labels = roundrobin(marker_labels, color_labels)

    ax = pylab.gca()
    lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5, -.07), loc='upper center', ncol=5)
    if plot_filename is not None:
        pu.savefig_legend_outside(plot_filename)
    else:
        pylab.ion()
        pylab.show()
    return fh

if __name__ == '__main__':
    # parse some arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vary_what', type=str, default='views')
    parser.add_argument('--input_filename', type=str, default='parsed_output')
    parser.add_argument('--plot_filename', type=str, default=None)
    args = parser.parse_args()
    input_filename = args.input_filename
    vary_what = args.vary_what
    plot_filename = args.plot_filename

    # configure parsing/plotting
    plot_parameters = plot_parameter_lookup[vary_what]
    which_kernel = plot_parameters['which_kernel']
    get_fixed_parameters = plot_parameters['get_fixed_parameters']
    get_variable_parameter = plot_parameters['get_variable_parameter']

    # some helper functions
    get_is_this_kernel = lambda timing_row: \
        timing_row.which_kernel == which_kernel
    is_one_view = lambda timing_row: timing_row.num_views == '1'

    # parse the timing data
    timing_rows = parse_timing_file(input_filename)
    these_timing_rows = filter(get_is_this_kernel, timing_rows)
    # these_timing_rows = filter(is_one_view, these_timing_rows)
    dict_of_dicts = group_results(these_timing_rows, get_fixed_parameters,
                                  get_variable_parameter)
    
    # plot
    plot_grouped_data(dict_of_dicts, plot_parameters, plot_filename)

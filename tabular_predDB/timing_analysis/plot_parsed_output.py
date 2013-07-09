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
#
def parse_timing_file(filename):
    header, rows = du.read_csv(filename)
    _timing_row = namedtuple('timing_row', ' '.join(header))
    timing_rows = []
    for row in rows:
        do_strip = lambda string: string.strip()
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

num_cols_to_color = {'4':'b', '16':'r', '32':'k'}
num_rows_to_color = {'100':'b', '400':'r', '1000':'k', '4000':'y', '10000':'g'}
num_clusters_to_marker = {'10':'x', '20':'o', '50':'v'}
#
plot_parameter_lookup = dict(
    row_partition_assignments=dict(
        which_kernel='row_partition_assignments',
        get_fixed_parameters=lambda timing_row: \
            (timing_row.num_cols, timing_row.num_clusters,
             timing_row.num_views),
        get_variable_parameter=get_num_rows,
        get_color_parameter=get_num_cols,
        color_dict=num_cols_to_color,
        ),
    column_partition_assignments=dict(
        which_kernel='column_partition_assignments',
        get_fixed_parameters=lambda timing_row: \
            (timing_row.num_rows, timing_row.num_clusters,
             timing_row.num_views),
        get_variable_parameter=get_num_cols,
        get_color_parameter=get_num_rows,
        color_dict=num_rows_to_color,
        )
    )

def plot_grouped_data(dict_of_dicts, timing_row_to_color, save_filename=None):
    pylab.figure()
    for configuration, run_data in dict_of_dicts.iteritems():
        x = sorted(run_data.keys())
        _y = [run_data[el] for el in x]
        y = map(get_time_per_step, _y)
        #
        plot_args = dict()
        first_timing_row = run_data.values()[0]
        color = timing_row_to_color(first_timing_row)
        plot_args['color'] = color
        marker = num_clusters_to_marker[first_timing_row.num_clusters]
        plot_args['marker'] = marker
        label = str(configuration)
        plot_args['label'] = label
        #
        pylab.plot(x, y, **plot_args)
    fh = pu.legend_outside(bbox_to_anchor=(0.5, -.05), ncol=4)
    if save_filename is not None:
        pu.savefig_legend_outside(save_filename)
    return fh

if __name__ == '__main__':
    # parse some arguments
    parser = argparse.ArgumentParser()
#    parser.add_argument('--plot_which_kernel', type=str, default='row_partition_assignments')
    parser.add_argument('--plot_which_kernel', type=str, default='column_partition_assignments')
    parser.add_argument('--filename', type=str, default='parsed_output')
    args = parser.parse_args()
    filename = args.filename
    plot_which_kernel = args.plot_which_kernel

    # configure parsing/plotting
    plot_parameters = plot_parameter_lookup[plot_which_kernel]
    get_fixed_parameters = plot_parameters['get_fixed_parameters']
    get_variable_parameter = plot_parameters['get_variable_parameter']
    get_color_parameter = plot_parameters['get_color_parameter']
    color_dict = plot_parameters['color_dict']

    # some helper functions
    get_is_this_kernel = lambda timing_row: \
        timing_row.which_kernel == plot_which_kernel
    is_one_view = lambda timing_row: timing_row.num_views == '1'
    timing_row_to_color = lambda timing_row: \
        color_dict[get_color_parameter(timing_row)]

    # parse the timing data
    timing_rows = parse_timing_file(filename)
    these_timing_rows = filter(get_is_this_kernel, timing_rows)
    these_timing_rows = filter(is_one_view, these_timing_rows)
    dict_of_dicts = group_results(these_timing_rows, get_fixed_parameters,
                                  get_variable_parameter)
    
    # plot
    plot_grouped_data(dict_of_dicts, timing_row_to_color)
    pylab.ion()
    pylab.show()

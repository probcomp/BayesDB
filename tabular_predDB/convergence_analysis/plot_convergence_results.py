import csv
import argparse
import collections
#
import pylab
pylab.ion()
pylab.show()


# settings
run_key_fields = ['num_rows', 'num_cols', 'num_clusters', 'num_views', 'max_mean']
dict_subset_keys = ['column_ari_list', 'mean_test_ll_list',
        'elapsed_seconds_list']


# set up some helper functions
def get_dict_values_subset(in_dict, keys_subset):
    values_subset = [in_dict[key] for key in keys_subset]
    return values_subset

def get_dict_subset(in_dict, keys_subset):
    values_subset = get_dict_values_subset(in_dict, keys_subset)
    dict_subset = dict(zip(keys_subset, values_subset))
    return dict_subset

def _get_run_key(line_dict):
    values = get_dict_values_subset(line_dict, run_key_fields)
    run_key = tuple(values)
    return run_key

def _get_run_key_dummy(line_dict):
    return 'all'

def get_default_dict():
    ret_dict = dict((key, list()) for key in dict_subset_keys)
    ret_dict['iter_idx_list'] = list()
    return ret_dict

def update_convergence_metrics(convergence_metrics, new_values_dict):
    for key, value in new_values_dict.iteritems():
        convergence_metrics[key].append(value)
    return convergence_metrics

def get_iter_indices(line_dict):
    n_steps = line_dict['n_steps']
    block_size = line_dict['block_size']
    num_blocks = n_steps / block_size + 1
    iter_indices = pylab.arange(num_blocks) * block_size
    return iter_indices

def plot_convergence_metrics(convergence_metrics, title_append='',
        x_is_iters=False, save_filename=None):
    x_variable = None
    x_label = None
    if x_is_iters:
        x_variable = pylab.array(convergence_metrics['iter_idx_list']).T
        x_label = 'iter idx'
    else:
        x_variable = pylab.array(convergence_metrics['elapsed_seconds_list']).T
        x_variable = x_variable.cumsum(axis=0)
        x_label = 'cumulative time (seconds)'
    ari_arr = pylab.array(convergence_metrics['column_ari_list']).T
    mean_test_ll_arr = pylab.array(convergence_metrics['mean_test_ll_list']).T
    #
    fh = pylab.figure()
    pylab.subplot(211)
    pylab.title('convergence diagnostics: %s' % title_append)
    pylab.plot(x_variable, ari_arr)
    pylab.xlabel(x_label)
    pylab.ylabel('column ARI')
    pylab.subplot(212)
    pylab.plot(x_variable, mean_test_ll_arr)
    pylab.xlabel(x_label)
    pylab.ylabel('mean test log likelihood')
    #
    if save_filename is not None:
      pylab.savefig(save_filename)
    return fh

def parse_convergence_metrics_csv(filename, get_run_key=_get_run_key):
    convergence_metrics_dict = collections.defaultdict(get_default_dict)
    with open(filename) as fh:
        csv_reader = csv.reader(fh)
        header = csv_reader.next()
        for line in csv_reader:
            evaled_line = map(eval, line)
            line_dict = dict(zip(header, evaled_line))
            run_key = get_run_key(line_dict)
            convergence_metrics = convergence_metrics_dict[run_key]
            new_values_dict = get_dict_subset(line_dict, dict_subset_keys) 
            new_values_dict['iter_idx_list'] = get_iter_indices(line_dict)
            update_convergence_metrics(convergence_metrics, new_values_dict)
    return convergence_metrics_dict

def filter_join(in_list, joinwith):
    in_list = filter(None, in_list)
    return joinwith.join(in_list)


if __name__ == '__main__':
    # parse some arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str)
    parser.add_argument('-one_plot', action='store_true')
    parser.add_argument('-x_is_iters', action='store_true')
    parser.add_argument('-do_save', action='store_true')
    parser.add_argument('--save_filename_prefix', type=str, default=None)
    #
    args = parser.parse_args()
    filename = args.filename
    one_plot = args.one_plot
    x_is_iters = args.x_is_iters
    do_save = args.do_save
    save_filename_prefix = args.save_filename_prefix
    #
    get_run_key = _get_run_key
    if one_plot:
        get_run_key = _get_run_key_dummy

    # parse the csv
    convergence_metrics_dict = parse_convergence_metrics_csv(filename)

    # actually plot
    fh_list = []
    save_filename = None
    for run_key, convergence_metrics in convergence_metrics_dict.iteritems():
      if do_save:
        n_bins = 20
        cumulative = True
        #
        filename_parts = [save_filename_prefix, str(run_key), 'timeseries.png']
        timeseries_save_filename = filter_join(filename_parts, '_')
        filename_parts = [save_filename_prefix, str(run_key), 'test_ll_hist.png']
        test_ll_hist_save_filename = filter_join(filename_parts, '_')
        filename_parts = [save_filename_prefix, str(run_key), 'runtime_hist.png']
        runtime_hist_save_filename = filter_join(filename_parts, '_')
        #
        pylab.figure()
        test_lls = pylab.array(convergence_metrics['mean_test_ll_list'])
        final_test_lls = test_lls[:, -1]
        pylab.hist(final_test_lls, n_bins, cumulative=cumulative)
        pylab.savefig(test_ll_hist_save_filename)
        #
        pylab.figure()
        final_times = pylab.array(convergence_metrics['elapsed_seconds_list']).T
        final_times = final_times.cumsum(axis=0)
        final_times = final_times[-1, :]
        pylab.hist(final_times, n_bins, cumulative=cumulative)
        pylab.savefig(runtime_hist_save_filename)
      fh = plot_convergence_metrics(convergence_metrics,
          title_append=str(run_key), x_is_iters=x_is_iters,
          save_filename=timeseries_save_filename)
      fh_list.append(fh)
      #


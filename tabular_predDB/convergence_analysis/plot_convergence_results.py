import csv
import argparse
import collections
#
import pylab
pylab.ion()
pylab.show()


# set up some helper functions
def get_dict_values_subset(in_dict, keys_subset):
    values_subset = [in_dict[key] for key in keys_subset]
    return values_subset

def get_dict_subset(in_dict, keys_subset):
    values_subset = get_dict_values_subset(in_dict, keys_subset)
    dict_subset = dict(zip(keys_subset, values_subset))
    return dict_subset

def _get_run_key(line_dict):
    fields = ['num_rows', 'num_cols', 'num_clusters', 'num_views']
    values = get_dict_values_subset(line_dict, fields)
    run_key = tuple(values)
    return run_key

def _get_run_key_dummy(line_dict):
    return 'all'

def get_default_dict():
    return dict(column_ari_list=list(), mean_test_ll_list=list(), iter_idx_list=list())

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

def plot_convergence_metrics(convergence_metrics, title_append=''):
    iter_idx_arr = pylab.array(convergence_metrics['iter_idx_list']).T
    ari_arr = pylab.array(convergence_metrics['column_ari_list']).T
    mean_test_ll_arr = pylab.array(convergence_metrics['mean_test_ll_list']).T
    #
    fh = pylab.figure()
    pylab.subplot(211)
    pylab.title('convergence diagnostics: %s' % title_append)
    pylab.plot(iter_idx_arr, ari_arr)
    pylab.xlabel('iter idx')
    pylab.ylabel('column ARI')
    pylab.subplot(212)
    pylab.plot(iter_idx_arr, mean_test_ll_arr)
    pylab.xlabel('iter idx')
    pylab.ylabel('mean test log likelihood')
    return fh


# parse some arguments
parser = argparse.ArgumentParser()
parser.add_argument('filename', type=str)
parser.add_argument('-one_plot', action='store_true')
args = parser.parse_args()
filename = args.filename
one_plot = args.one_plot
#
get_run_key = _get_run_key
if one_plot:
    get_run_key = _get_run_key_dummy


# parse the csv
convergence_metrics_dict = collections.defaultdict(get_default_dict)
with open(filename) as fh:
    csv_reader = csv.reader(fh)
    header = csv_reader.next()
    for line in csv_reader:
        evaled_line = map(eval, line)
        line_dict = dict(zip(header, evaled_line))
        run_key = get_run_key(line_dict)
        convergence_metrics = convergence_metrics_dict[run_key]
        new_values_dict = get_dict_subset(line_dict, ['column_ari_list', 'mean_test_ll_list'])
        new_values_dict['iter_idx_list'] = get_iter_indices(line_dict)
        update_convergence_metrics(convergence_metrics, new_values_dict)


# actually plot
fh_list = []
for run_key, convergence_metrics in convergence_metrics_dict.iteritems():
    fh = plot_convergence_metrics(convergence_metrics, title_append=str(run_key))
    fh_list.append(fh)

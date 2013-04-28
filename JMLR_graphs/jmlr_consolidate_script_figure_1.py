import os
import argparse
from collections import defaultdict
#
import pylab
import numpy
#
import tabular_predDB.python_utils.file_utils as fu


parser = argparse.ArgumentParser()
parser.add_argument('num_views', type=int)
parser.add_argument('gen_seed', type=int)
parser.add_argument('directory', default='.', type=str)
args = parser.parse_args()
num_views = args.num_views
gen_seed = args.gen_seed
directory = args.directory
#
str_args = (num_views, gen_seed)
save_filename_prefix = 'num_views_%s_gen_seed_%s' % str_args

def set_lim(ax, xmin=None, xmax=None, ymin=None, ymax=None):
    if xmin is not None or xmax is not None:
        if xmin is None:
            xmin = ax.get_xlim()[0]
        if xmax is None:
            xmax = ax.get_xlim()[1]
        ax.set_xlim((xmin, xmax))
    if ymin is not None or ymax is not None:
        if ymin is None:
            ymin = ax.get_ylim()[0]
        if ymax is None:
            ymax = ax.get_ylim()[1]
        ax.set_ylim((ymin, ymax))
    return

color_lookup = dict(
    from_the_prior='b',
    apart='r',
    together='k',
    )
def plot(num_views_list_dict, seconds_since_start_list_dict, filename=None):
    fig = pylab.figure()
    keys = num_views_list_dict.keys()
    # #views vs iterations, zoomed out
    line_lookup = dict()
    ax = pylab.subplot(221)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        iter_idx = map(lambda x: range(len(x)), seconds_since_start_list)
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(numpy.array(iter_idx).T,
                           numpy.array(num_views_list).T,
                           label=initialization, color=color)
        line_lookup[initialization] = lines[0]
    set_lim(ax, xmax=3600)
    pylab.xlabel('iteration #')
    pylab.ylabel('num_views')
    lines = [line_lookup[initialization] for initialization in keys]
    pylab.legend(lines, keys)
    # #views vs iterations, zoomed in
    line_lookup = dict()
    ax = pylab.subplot(222)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        iter_idx = map(lambda x: range(len(x)), seconds_since_start_list)
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(numpy.array(iter_idx).T,
                           numpy.array(num_views_list).T,
                           label=initialization, color=color)
        line_lookup[initialization] = lines[0]
    set_lim(ax, xmax=3600, ymax=15)
    pylab.xlabel('iteration #')
    pylab.ylabel('num_views')
    lines = [line_lookup[initialization] for initialization in keys]
    pylab.legend(lines, keys)
    # #views vs seconds, zoomed out
    line_lookup = dict()
    ax = pylab.subplot(223)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(numpy.array(seconds_since_start_list).T,
                           numpy.array(num_views_list).T,
                           label=initialization, color=color)
        line_lookup[initialization] = lines[0]
    set_lim(ax, xmax=3600)
    pylab.xlabel('cumulative run time (seconds)')
    pylab.ylabel('num_views')
    lines = [line_lookup[initialization] for initialization in keys]
    pylab.legend(lines, keys)
    # #views vs seconds, zoomed in
    line_lookup = dict()
    ax = pylab.subplot(224)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(numpy.array(seconds_since_start_list).T,
                           numpy.array(num_views_list).T,
                           label=initialization, color=color)
        line_lookup[initialization] = lines[0]
    set_lim(ax, xmax=3600, ymax=15)
    pylab.xlabel('cumulative run time (seconds)')
    pylab.ylabel('num_views')
    lines = [line_lookup[initialization] for initialization in keys]
    pylab.legend(lines, keys)
    #
    if filename is not None:
        pylab.savefig(save_filename_prefix)

all_files = os.listdir(directory)
is_this_config = lambda filename: filename.startswith(save_filename_prefix)
is_pkl = lambda filename: filename.endswith('.pkl.gz') or filename.endswith('.pkl')
these_files = filter(is_pkl, filter(is_this_config, all_files))

seconds_since_start_list_dict = defaultdict(list)
num_views_list_dict = defaultdict(list)
for this_file in these_files:
    unpickled = fu.unpickle(this_file, dir=directory)
    for initialization, seconds_since_start_list \
            in unpickled['seconds_since_start_list_dict'].iteritems():
        seconds_since_start_list_dict[initialization].append(seconds_since_start_list)
    for initialization, num_views_list \
            in unpickled['num_views_list_dict'].iteritems():
        num_views_list_dict[initialization].append(num_views_list)

plot(num_views_list_dict, seconds_since_start_list_dict)

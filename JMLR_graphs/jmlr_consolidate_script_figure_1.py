import os
import copy
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

def rectangularize_with_nans(ragged):
    num_rows = len(ragged)
    num_cols = max(map(len, ragged))
    shape = (num_rows, num_cols)
    arr = numpy.ones(shape) * numpy.nan
    #
    for row_idx, row in enumerate(ragged):
        row_len = len(row)
        arr[row_idx, range(row_len)] = row
    return arr

def get_unique_handles_labels(handles, labels):
    handles_lookup = dict()
    for handle, label in zip(handles, labels):
        if label not in handles_lookup:
            handles_lookup[label] = handle
    unique_labels = handles_lookup.keys()
    unique_handles = handles_lookup.values()
    return unique_handles, unique_labels

def legend_outside(ax=None, bbox_to_anchor=(0.5, -.25), loc='upper center',
                   ncol=None, unique=True, cmp_func=cmp):
    # labels must be set in original plot call: plot(..., label=label)
    if ax is None:
        ax = pylab.gca()
    handles, labels = ax.get_legend_handles_labels()
    if unique:
        handles, labels = get_unique_handles_labels(handles, labels)
    zipped = zip(handles, labels)
    cmp_func_mod = lambda x, y: cmp_func(x[-1], y[-1])
    sorted_zipped = sorted(zipped, cmp=cmp_func_mod)[::-1]
    handles, labels = zip(*sorted_zipped)
    handles = pylab.array(handles)
    handle_copies = [copy.copy(handle) for handle in handles]
    for handle in handle_copies:
        handle.set_alpha(1.0)
    labels = pylab.array(labels)
    if ncol is None:
        ncol = min(len(labels), 3)
    # lgd = ax.legend(handles, labels, loc=loc, ncol=ncol,
    # 	            bbox_to_anchor=bbox_to_anchor, prop={"size":14})
    lgd = pylab.legend(handle_copies, labels, loc=loc, ncol=ncol,
                       bbox_to_anchor=bbox_to_anchor, prop={"size":14})

def savefig_legend_outside(namestr, ax=None, bbox_inches='tight', bbox_extra_artists=()):
    if ax is None:
        ax = pylab.gca()
    lgd = ax.get_legend()
    if bbox_extra_artists is None:
        bbox_extra_artists = (lgd,)
    else:
        bbox_extra_artists = list(bbox_extra_artists)
        bbox_extra_artists.append(lgd)
    try:
        pylab.savefig(namestr, bbox_extra_artists=bbox_extra_artists,
                      bbox_inches=bbox_inches)
    except Exception, e:
        print e
        pylab.savefig(namestr)

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
    ax = pylab.subplot(221)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        iter_idx = map(lambda x: range(len(x)), seconds_since_start_list)
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(rectangularize_with_nans(iter_idx).T,
                           rectangularize_with_nans(num_views_list).T,
                           label=initialization, color=color, alpha=0.3)
    # set_lim(ax, xmax=3600)
    ax.set_xticks(ax.get_xticks()[::2])
    pylab.xlabel('iteration #')
    pylab.ylabel('# views')
    # #views vs iterations, zoomed in
    ax = pylab.subplot(222)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        iter_idx = map(lambda x: range(len(x)), seconds_since_start_list)
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(rectangularize_with_nans(iter_idx).T,
                           rectangularize_with_nans(num_views_list).T,
                           label=initialization, color=color, alpha=0.3)
    set_lim(ax, ymax=15)
    ax.set_xticks(ax.get_xticks()[::2])
    pylab.xlabel('iteration #')
    pylab.ylabel('# views')
    # #views vs seconds, zoomed out
    ax = pylab.subplot(223)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(rectangularize_with_nans(seconds_since_start_list).T,
                           rectangularize_with_nans(num_views_list).T,
                           label=initialization, color=color, alpha=0.3)
    set_lim(ax, xmax=3600)
    ax.set_xticks([0, 1000, 2000, 3000])
    pylab.xlabel('cumulative run time (seconds)')
    pylab.ylabel('# views')
    # #views vs seconds, zoomed in
    ax = pylab.subplot(224)
    for initialization in keys:
        seconds_since_start_list = seconds_since_start_list_dict[initialization]
        num_views_list = num_views_list_dict[initialization]
        color = color_lookup[initialization]
        lines = pylab.plot(rectangularize_with_nans(seconds_since_start_list).T,
                           rectangularize_with_nans(num_views_list).T,
                           label=initialization, color=color, alpha=0.3)
    set_lim(ax, xmax=3600, ymax=15)
    ax.set_xticks([0, 1000, 2000, 3000])
    pylab.xlabel('cumulative run time (seconds)')
    pylab.ylabel('# views')
    legend_outside(bbox_to_anchor=(-.15, -.25))
    #
    title_str = 'Initializing the sampler from the prior ensures reliable convergence in a reasonable amount of time.\nGround truth #views is %d' % num_views
    ft = pylab.figtext(0.5, 0.94, title_str,
                  ha='center', color='black', weight='bold', size='small')
    if filename is not None:        
        pylab.savefig(save_filename_prefix)
    return ft

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

ft = plot(num_views_list_dict, seconds_since_start_list_dict)
plot_filename = 'num_views_%d' % num_views
savefig_legend_outside(plot_filename, bbox_extra_artists=[ft])
pylab.ion()
pylab.show()

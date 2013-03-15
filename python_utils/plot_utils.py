import os
#
import pylab
import numpy


def my_savefig(filename, dir=''):
    if filename is not None:
        full_filename = os.path.join(dir, filename)
        pylab.savefig(full_filename)
        pylab.close()

def get_aspect_ratio(T_array):
    num_rows = len(T_array)
    num_cols = len(T_array[0])
    aspect_ratio = float(num_cols)/num_rows
    return aspect_ratio

def plot_T(T_array, filename=None, dir=''):
    aspect_ratio = get_aspect_ratio(T_array)
    pylab.figure()
    pylab.imshow(T_array, aspect=aspect_ratio, interpolation='none')
    my_savefig(filename, dir)

def plot_views(T_array, X_D, X_L, filename=None, dir=''):
     pylab.figure()
     view_assignments = X_L['column_partition']['assignments']
     view_assignments = numpy.array(view_assignments)
     num_views = len(set(view_assignments))
     for view_idx in range(num_views):
          X_D_i = X_D[view_idx]
          argsorted = numpy.argsort(X_D_i)
          is_this_view = view_assignments==view_idx
          xticklabels = numpy.nonzero(is_this_view)[0]
          num_cols_i = sum(is_this_view)
          T_array_sub = T_array[:,is_this_view][argsorted]
          aspect_ratio = get_aspect_ratio(T_array_sub)
          pylab.subplot(1, num_views, view_idx + 1)
          pylab.imshow(T_array_sub, aspect=aspect_ratio,
                       interpolation='none')
          pylab.gca().set_xticks(range(num_cols_i))
          pylab.gca().set_xticklabels(map(str, xticklabels))
          if view_idx!=0: pylab.gca().set_yticklabels([])
     my_savefig(filename, dir)

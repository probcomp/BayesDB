#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import os
#
import numpy
import pylab
pylab.ion()
import hcluster
#
import tabular_predDB.python_utils.general_utils as gu


def my_savefig(filename, dir='', close=True):
    if filename is not None:
        full_filename = os.path.join(dir, filename)
        pylab.savefig(full_filename)
        if close:
            pylab.close()

def get_aspect_ratio(T_array):
    num_rows = len(T_array)
    num_cols = len(T_array[0])
    aspect_ratio = float(num_cols)/num_rows
    return aspect_ratio

def plot_T(T_array, M_c, filename=None, dir='', close=True):
    num_cols = len(T_array[0])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)

    aspect_ratio = get_aspect_ratio(T_array)
    pylab.figure()
    pylab.imshow(T_array, aspect=aspect_ratio, interpolation='none',
                 cmap=pylab.matplotlib.cm.Greens)
    pylab.gca().set_xticks(range(num_cols))
    pylab.gca().set_xticklabels(column_names, rotation=90, size='x-small')

    pylab.show()
    
    my_savefig(filename, dir, close)

def plot_views(T_array, X_D, X_L, M_c, filename=None, dir='', close=True):

    num_cols = len(X_L['column_partition']['assignments'])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)

    fig = pylab.figure()
    view_assignments = X_L['column_partition']['assignments']
    view_assignments = numpy.array(view_assignments)
    num_features = len(view_assignments)
    num_views = len(set(view_assignments))
    
    disLeft = 0.1
    disRight = 0.1
    viewSpacing = 0.1/(max(2,num_views)-1)
    nxtAxDisLeft = disLeft
    axpos2 = 0.2
    axpos4 = 0.75
    
    for view_idx in range(num_views):
        X_D_i = X_D[view_idx]
        argsorted = numpy.argsort(X_D_i)
        is_this_view = view_assignments==view_idx
        xticklabels = numpy.nonzero(is_this_view)[0]
        num_cols_i = sum(is_this_view)
        T_array_sub = T_array[:,is_this_view][argsorted]
        nxtAxWidth = (float(num_cols_i)/num_features)*(1-viewSpacing*(num_views-1.)-disLeft-disRight)
        axes_pos = nxtAxDisLeft, axpos2, nxtAxWidth, axpos4
        currax = fig.add_axes(axes_pos)
        nxtAxDisLeft = nxtAxDisLeft+nxtAxWidth+viewSpacing
        aspect_ratio = get_aspect_ratio(T_array)
        
        # Normalize each column to display
        mincols = T_array_sub.min(axis=0)
        maxcols = T_array_sub.max(axis=0)
        T_norm = (T_array_sub-mincols[numpy.newaxis,:])/(maxcols[numpy.newaxis,:]-mincols[numpy.newaxis,:])
        pylab.imshow(T_norm, aspect = 'auto',
                     interpolation='none',cmap=pylab.matplotlib.cm.Greens)
        old_tmp = 0
        
        for y in range(max(X_D_i)):
            tmp = numpy.sum([X_D_i[x] == y for x in range(len(X_D_i))])
            if tmp > 5:
                pylab.plot(numpy.arange(num_cols_i+1)-0.5, [old_tmp+tmp]*(num_cols_i+1),color='red',linewidth=2,hold='true')
            old_tmp = old_tmp+tmp
               
        pylab.gca().set_xticks(range(num_cols_i))
        #pylab.gca().set_xticklabels(map(str, xticklabels))
        #pdb.set_trace()
        pylab.gca().set_xticklabels(column_names[is_this_view], rotation=90, size='x-small')
        pylab.gca().set_yticklabels([])
        pylab.xlim([-0.5, num_cols_i-0.5])
        pylab.ylim([0, len(T_array_sub)])

        pylab.show()
        if view_idx!=0: pylab.gca().set_yticklabels([])
    my_savefig(filename, dir, close)

def plot_predicted_value(value, samples, modelType, filename='imputed_value_hist.png', plotcolor='red', truth=None, x_axis_lim=None):

    fig = pylab.figure()
    # Find 50% bounds
    curr_std = numpy.std(samples)
    curr_delta = 2*curr_std/100;
    ndraws = len(samples)
    
    for thresh in numpy.arange(curr_delta, 2*curr_std, curr_delta):
        withinbounds = len([i for i in range(len(samples)) if samples[i] < (value+thresh) and samples[i] > (value-thresh)])
        if float(withinbounds)/ndraws > 0.5:
            break

    bounds = [value-thresh, value+thresh]
    
    # Plot histogram
    # 'normal_inverse_gamma': continuous_imputation,
    # 'symmetric_dirichlet_discrete': multinomial_imputation,
    
    if modelType == 'normal_inverse_gamma':
        nx, xbins, rectangles = pylab.hist(samples,bins=40,normed=0,color=plotcolor)
    elif modelType == 'symmetric_dirichlet_discrete':
        bin_edges = numpy.arange(numpy.min(samples)-0.5, numpy.max(samples)-0.5, 1)  
        nx, xbins, rectangles = pylab.hist(samples,bin_edges,normed=0,color=plotcolor)
    else:
        print 'Unsupported model type'

    pylab.clf()

    nx_frac = nx/float(sum(nx))
    x_width = [(xbins[i+1]-xbins[i]) for i in range(len(xbins)-1)]
    pylab.bar(xbins[0:len(xbins)-1],nx_frac,x_width,color=plotcolor)
    pylab.plot([value, value],[0,1], color=plotcolor, hold=True,linewidth=2)                      
    pylab.plot([bounds[0], bounds[0]],[0,1], color=plotcolor, hold=True, linestyle='--',linewidth=2)
    pylab.plot([bounds[1], bounds[1]],[0,1], color=plotcolor, hold=True, linestyle='--',linewidth=2)
    if truth != None:
        pylab.plot([truth, truth],[0,1], color='green', hold=True, linestyle='--',linewidth=2)
    pylab.show()

    if x_axis_lim != None:
        pylab.xlim(x_axis_lim)
    my_savefig(filename, '', False)
    return pylab.gca().get_xlim()

def do_gen_feature_z(X_L_list, X_D_list, M_c, filename, tablename=''):
    num_cols = len(X_L_list[0]['column_partition']['assignments'])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)
    # extract unordered z_matrix
    num_latent_states = len(X_L_list)
    z_matrix = numpy.zeros((num_cols, num_cols))
    for X_L in X_L_list:
      assignments = X_L['column_partition']['assignments']
      for i in range(num_cols):
        for j in range(num_cols):
          if assignments[i] == assignments[j]:
            z_matrix[i, j] += 1
    z_matrix /= float(num_latent_states)
    # hierachically cluster z_matrix
    Y = hcluster.pdist(z_matrix)
    Z = hcluster.linkage(Y)
    pylab.figure()
    hcluster.dendrogram(Z)
    intify = lambda x: int(x.get_text())
    reorder_indices = map(intify, pylab.gca().get_xticklabels())
    pylab.close()
    # REORDER! 
    z_matrix_reordered = z_matrix[:, reorder_indices][reorder_indices, :]
    column_names_reordered = column_names[reorder_indices]
    # actually create figure
    fig = pylab.figure()
    fig.set_size_inches(16, 12)
    pylab.imshow(z_matrix_reordered, interpolation='none',
                 cmap=pylab.matplotlib.cm.Greens)
    pylab.colorbar()
    if num_cols < 14:
      pylab.gca().set_yticks(range(num_cols))
      pylab.gca().set_yticklabels(column_names_reordered, size='x-small')
      pylab.gca().set_xticks(range(num_cols))
      pylab.gca().set_xticklabels(column_names_reordered, rotation=90, size='x-small')
    else:
      pylab.gca().set_yticks(range(num_cols)[::2])
      pylab.gca().set_yticklabels(column_names_reordered[::2], size='x-small')
      pylab.gca().set_xticks(range(num_cols)[1::2])
      pylab.gca().set_xticklabels(column_names_reordered[1::2],
                                  rotation=90, size='small')
    pylab.title('column dependencies for: %s' % tablename)
    pylab.savefig(filename)

def legend_outside(ax=None, bbox_to_anchor=(0.5, -.25), loc='upper center',
                   ncol=None, label_cmp=None):
    # labels must be set in original plot call: plot(..., label=label)
    if ax is None:
        ax = pylab.gca()
    handles, labels = ax.get_legend_handles_labels()
    label_to_handle = dict(zip(labels, handles))
    labels = label_to_handle.keys()
    if label_cmp is not None:
        labels = sorted(labels, cmp=label_cmp)
    handles = [label_to_handle[label] for label in labels]
    if ncol is None:
        ncol = min(len(labels), 3)
    lgd = ax.legend(handles, labels, loc=loc, ncol=ncol,
                    bbox_to_anchor=bbox_to_anchor, prop={"size":14})
    return

int_cmp = lambda x, y: cmp(int(x), int(y))
def legend_outside_from_dicts(marker_dict, color_dict,
                              marker_prepend='', color_prepend='',
                              ax=None, bbox_to_anchor=(0.5, -.07), loc='upper center',
                              ncol=None, label_cmp=None,
                              marker_color='k'):
    marker_handles = []
    marker_labels = []
    for label in sorted(marker_dict.keys(), cmp=int_cmp):
        marker = marker_dict[label]
        handle = pylab.Line2D([],[], color=marker_color, marker=marker, linewidth=0)
        marker_handles.append(handle)
        marker_labels.append(marker_prepend+label)
    color_handles = []
    color_labels = []
    for label in sorted(color_dict.keys(), cmp=int_cmp):
        color = color_dict[label]
        handle = pylab.Line2D([],[], color=color, linewidth=3)
        color_handles.append(handle)
        color_labels.append(color_prepend+label)
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
    handles = gu.roundrobin(marker_handles, color_handles)
    labels = gu.roundrobin(marker_labels, color_labels)
    if ax is None:
        ax = pylab.gca()
    if ncol is None:
        ncol = max(num_marker_handles, num_color_handles)
    lgd = ax.legend(handles, labels, loc=loc, ncol=ncol,
                    bbox_to_anchor=bbox_to_anchor, prop={"size":14})
    return

def savefig_legend_outside(filename, ax=None, bbox_inches='tight'):
    if ax is None:
        ax = pylab.gca()
    lgd = ax.get_legend()
    pylab.savefig(filename,
                  bbox_extra_artists=(lgd,),
                  bbox_inches=bbox_inches,
                  )
    return

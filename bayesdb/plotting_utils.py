#
#   Copyright (c) 2010-2013, MIT Probabilistic Computing Project
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

import numpy
import os
import pylab
import matplotlib.cm

import utils
import crosscat.utils.data_utils as du

def plot_matrix(matrix, column_names, title='', filename=None):
    # actually create figure
    fig = pylab.figure()
    fig.set_size_inches(16, 12)
    pylab.imshow(matrix, interpolation='none',
                 cmap=matplotlib.cm.gray_r, vmin=0, vmax=1)
    pylab.colorbar()
    pylab.gca().set_yticks(range(len(column_names)))
    pylab.gca().set_yticklabels(column_names, size='small')
    pylab.gca().set_xticks(range(len(column_names)))
    pylab.gca().set_xticklabels(column_names, rotation=90, size='small')
    pylab.title(title)
    if filename or 'DISPLAY' not in os.environ.keys():
        pylab.savefig(filename)
    else:
        fig.show()


def _create_histogram(M_c, data, columns, mc_col_indices, filename):
  dir=S.path.web_resources_data_dir
  full_filename = os.path.join(dir, filename)
  num_rows = data.shape[0]
  num_cols = data.shape[1]
  #
  pylab.figure()
  # col_i goes from 0 to number of predicted columns
  # mc_col_idx is the original column's index in M_c
  for col_i in range(num_cols):
    mc_col_idx = mc_col_indices[col_i]
    data_i = data[:, col_i]
    ax = pylab.subplot(1, num_cols, col_i, title=columns[col_i])
    if M_c['column_metadata'][mc_col_idx]['modeltype'] == 'normal_inverse_gamma':
      pylab.hist(data_i, orientation='horizontal')
    else:
      str_data = [du.convert_code_to_value(M_c, mc_col_idx, code) for code in data_i]
      unique_labels = list(set(str_data))
      np_str_data = numpy.array(str_data)
      counts = []
      for label in unique_labels:
        counts.append(sum(np_str_data==label))
      num_vals = len(M_c['column_metadata'][mc_col_idx]['code_to_value'])
      rects = pylab.barh(range(num_vals), counts)
      heights = numpy.array([rect.get_height() for rect in rects])
      ax.set_yticks(numpy.arange(num_vals) + heights/2)
      ax.set_yticklabels(unique_labels)
  pylab.tight_layout()
  pylab.savefig(full_filename)

def _do_gen_matrix(col_function_name, X_L_list, X_D_list, M_c, T, tablename='', filename=None, col=None, confidence=None, limit=None, submatrix=False):
    if col_function_name == 'mutual information':
      col_function = utils._mutual_information
    elif col_function_name == 'dependence probability':
      col_function = utils._dependence_probability
    elif col_function_name == 'correlation':
      col_function = utils._correlation
    elif col_function_name == 'view_similarity':
      col_function = utils._view_similarity
    else:
      raise Exception('Invalid column function: %s' % col_function_name)

    num_cols = len(X_L_list[0]['column_partition']['assignments'])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)
    # extract unordered z_matrix
    num_latent_states = len(X_L_list)
    z_matrix = numpy.zeros((num_cols, num_cols))
    for i in range(num_cols):
      for j in range(num_cols):
        z_matrix[i][j] = col_function(i, j, X_L_list, X_D_list, M_c, T)

    if col:
      z_column = list(z_matrix[M_c['name_to_idx'][col]])
      data_tuples = zip(z_column, range(num_cols))
      data_tuples.sort(reverse=True)
      if confidence:
        data_tuples = filter(lambda tup: tup[0] >= float(confidence), data_tuples)
      if limit and limit != float("inf"):
        data_tuples = data_tuples[:int(limit)]
      data = [tuple([d[0] for d in data_tuples])]
      columns = [d[1] for d in data_tuples]
      column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]      
      column_names = numpy.array(column_names)
      column_names_reordered = column_names[columns]
      if submatrix:
        z_matrix = z_matrix[columns,:][:,columns]
        z_matrix_reordered = z_matrix
      else:
        return {'data': data, 'columns': column_names_reordered}
    else:
      # hierachically cluster z_matrix
      import hcluster
      Y = hcluster.pdist(z_matrix)
      Z = hcluster.linkage(Y)
      pylab.figure()
      hcluster.dendrogram(Z)
      intify = lambda x: int(x.get_text())
      reorder_indices = map(intify, pylab.gca().get_xticklabels())
      pylab.clf() ## use instead of close to avoid error spam
      # REORDER! 
      z_matrix_reordered = z_matrix[:, reorder_indices][reorder_indices, :]
      column_names_reordered = column_names[reorder_indices]

    title = 'Pairwise column %s for %s' % (col_function_name, tablename)
    if filename:
      utils.plot_matrix(z_matrix_reordered, column_names_reordered, title, filename)

    return dict(
      matrix=z_matrix_reordered,
      column_names=column_names_reordered,
      title=title,
      filename=filename,
      message = "Created " + title
      )
        

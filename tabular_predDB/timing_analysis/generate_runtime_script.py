import itertools


n_steps = 10
#
base_str = ' '.join([
  'python runtime_scripting.py',
  '--num_clusters %s',
  '--num_rows %s',
  '--num_cols %s',
  '--num_splits %s',
  '--n_steps %s' % n_steps,
  '-do_remote >>out 2>>err &',
  ])

num_clusters_list = [5, 10, 20, 25, 40]
num_rows_list = [100, 400, 1000]
num_cols_list = [4, 10, 20, 40]
num_splits_list = [1, 2, 4]
take_product_of = [num_clusters_list, num_rows_list, num_cols_list, num_splits_list]
for num_clusters, num_rows, num_cols, num_splits \
    in itertools.product(*take_product_of):
  this_base_str = base_str % (num_clusters, num_rows, num_cols, num_splits)
  print this_base_str

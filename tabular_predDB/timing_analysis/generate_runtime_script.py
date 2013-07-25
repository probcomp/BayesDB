import itertools


n_steps = 10
#
base_str = ' '.join([
  'python runtime_scripting.py',
  '--num_rows %s',
  '--num_cols %s',
  '--num_clusters %s',
  '--num_splits %s',
  '--n_steps %s' % n_steps,
  '-do_local >>out 2>>err &',
  ])

# num_rows_list = [100, 400, 1000, 4000, 10000]
# num_cols_list = [4, 8, 16, 24, 32]
# num_clusters_list = [10, 20, 30, 40, 50]
# num_splits_list = [1, 2, 3, 4, 5]

num_rows_list = [100, 400]
num_cols_list = [4, 16]
num_clusters_list = [10, 20]
num_splits_list = [1, 2]

take_product_of = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list]
for num_rows, num_cols, num_clusters, num_splits \
    in itertools.product(*take_product_of):
  this_base_str = base_str % (num_rows, num_cols, num_clusters, num_splits)
  print this_base_str

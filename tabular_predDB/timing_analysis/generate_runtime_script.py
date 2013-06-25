import itertools


num_rows = 1000
num_cols = 20
n_steps = 200

base_str = ' '.join([
  'python runtime_scripting.py',
  '--num_clusters %s',
  '--num_rows %s' % num_rows,
  '--num_cols %s' % num_cols,
  '--num_splits %s',
  '--n_steps %s' % n_steps,
  '-do_remote >>out 2>>err &',
  ])

num_clusters_list = [5, 10, 20, 25, 40]
num_splits_list = [1, 2, 4]
for num_clusters, num_splits \
    in itertools.product(num_clusters_list, num_splits_list):
  this_base_str = base_str % (num_clusters, num_splits)
  print this_base_str

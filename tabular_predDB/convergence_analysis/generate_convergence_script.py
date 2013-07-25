import itertools
import csv
import os

ari_filename = 'ari_convergence_results.csv'
n_steps = 500
block_size = 20
run_script = False
#
base_str = ' '.join([
  'python convergence_test.py',
  '--max_rows %s',
  '--num_cols %s',
  '--num_clusters %s',
  '--num_views %s',
  '--block_size %s' % block_size,
  '--num_transitions %s' % n_steps,
  '--ari_logfile %s' % ari_filename,
  '>>out 2>>err',
  ])

# num_rows_list = [100, 400, 1000, 4000, 10000]
# num_cols_list = [4, 8, 16, 24, 32]
# num_clusters_list = [10, 20, 30, 40, 50]
# num_splits_list = [1, 2, 3, 4, 5]

num_rows_list = [200, 400]
num_cols_list = [4, 8]
num_clusters_list = [5, 10]
num_splits_list = [2,4]

# First create the headers in the output file - the convergence test script does not write headers
with open(ari_filename, 'w') as outfile:
  csvwriter=csv.writer(outfile,delimiter=',')
  header = ['Time', 'num_transitions', 'block_size', 'num_rows','num_cols','num_views','num_clusters','ari_views','ari_table']
  csvwriter.writerow(header)

outfile.close()
count = 0
script_name = 'convergence_testing_script.sh'
with open(script_name, 'w') as script_file:
    take_product_of = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list]
    for num_rows, num_cols, num_clusters, num_splits \
        in itertools.product(*take_product_of):
        this_base_str = base_str % (num_rows, num_cols, num_clusters, num_splits)
        print this_base_str
        count = count + 1
        script_file.write(this_base_str + '\n')

script_file.close()

if run_script:
  os.system('bash convergence_testing_script.sh')

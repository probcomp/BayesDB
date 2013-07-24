import argparse, pylab, numpy, pdb
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.CrossCatClient as ccc
import tabular_predDB.python_utils.file_utils as f_utils
import tabular_predDB.python_utils.timing_test_utils as ttu
from time import time

# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--filename', default=None,
                    type=str)
parser.add_argument('--ari_logfile', default='daily_ari_logs.csv',
                    type=str)
parser.add_argument('--inf_seed', default=0, type=int)
parser.add_argument('--gen_seed', default=0, type=int)
parser.add_argument('--num_transitions', default=500, type=int)
parser.add_argument('--N_GRID', default=31, type=int)
parser.add_argument('--max_rows', default=400, type=int)
parser.add_argument('--num_clusters', default=10, type=int)
parser.add_argument('--num_views', default=2, type=int)
parser.add_argument('--num_cols', default=16, type=int)
parser.add_argument('--numChains',default=50, type = int)
parser.add_argument('--block_size',default=20, type = int)

args = parser.parse_args()
filename = args.filename
ari_logfile = args.ari_logfile
inf_seed = args.inf_seed
gen_seed = args.gen_seed
num_transitions = args.num_transitions
N_GRID = args.N_GRID
max_rows = args.max_rows
num_clusters = args.num_clusters
num_views = args.num_views
num_cols = args.num_cols
numChains = args.numChains
block_size = args.block_size

engine = ccc.get_CrossCatClient('hadoop', seed = inf_seed)

if filename is not None:
    # Load the data from table and sub-sample entities to max_rows
    T, M_r, M_c = du.read_model_data_from_csv(filename, max_rows, gen_seed,cctypes = cctypes)
    truth_flag = 0
else:
    T, M_r, M_c, data_inverse_permutation_indices = \
        du.gen_factorial_data_objects(gen_seed, num_clusters,
                                      num_cols, max_rows, num_views,
                                      max_mean=10, max_std=1,
                                      send_data_inverse_permutation_indices=True)
        view_assignment_truth, X_D_truth = ttu.truth_from_permute_indices(data_inverse_permutation_indices, max_rows,num_cols,num_views, num_clusters)
        truth_flag = 1


        
T_array = numpy.asarray(T)
num_rows = len(T)
num_cols = len(T[0])

ari_table = []
ari_views = []

print 'Initializing ...'
# Call Initialize and Analyze
M_c, M_r, X_L_list, X_D_list = engine.initialize(M_c, M_r, T, n_chains = numChains)
if truth_flag:
    tmp_ari_table, tmp_ari_views = ttu.multi_chain_ARI(X_L_list,X_D_list, view_assignment_truth, X_D_truth)
    ari_table.append(tmp_ari_table)
    ari_views.append(tmp_ari_views)
            
completed_transitions = 0

n_steps = min(block_size, num_transitions)
print 'Analyzing ...'
while (completed_transitions < num_transitions):
    # We won't be limiting by time in the convergence runs
    X_L_list, X_D_list = engine.analyze(M_c, T, X_L_list, X_D_list, kernel_list=(),
                                        n_steps=n_steps, max_time=-1)
    
    if truth_flag:
        tmp_ari_table, tmp_ari_views = ttu.multi_chain_ARI(X_L_list,X_D_list, view_assignment_truth, X_D_truth)
        ari_table.append(tmp_ari_table)
        ari_views.append(tmp_ari_views)
        
    completed_transitions = completed_transitions+block_size
    print completed_transitions
    saved_dict = {'T':T, 'M_c':M_c, 'X_L_list':X_L_list, 'X_D_list': X_D_list}
    pkl_filename = 'model_{!s}.pkl.gz'.format(str(completed_transitions))
    f_utils.pickle(saved_dict, filename = pkl_filename)
    
saved_dict = {'T':T, 'M_c':M_c, 'X_L_list':X_L_list, 'X_D_list': X_D_list}
pkl_filename = 'model_{!s}.pkl.gz'.format('last')
f_utils.pickle(saved_dict, filename = pkl_filename)

with open(ari_logfile, 'a') as outfile:
    csvwriter=csv.writer(outfile,delimiter=',')
    csvwriter.writerow([time.ctime(), ari_views, ari_table])

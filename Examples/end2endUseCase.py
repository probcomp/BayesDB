import argparse, pylab, numpy, pdb
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.CrossCatClient as ccc
import tabular_predDB.python_utils.file_utils as f_utils
import tabular_predDB.python_utils.useCase_utils as uc_utils

from time import time


# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--filename', default='kiva_flat_table_medium.csv',
                    type=str)
parser.add_argument('--inf_seed', default=int(time()), type=int)
parser.add_argument('--gen_seed', default=int(time())+1, type=int)
parser.add_argument('--num_transitions', default=100, type=int)
parser.add_argument('--N_GRID', default=31, type=int)
parser.add_argument('--max_rows', default=5000, type=int)
parser.add_argument('--numDraws', default=25, type=int)
parser.add_argument('--numChains',default=50, type = int)
parser.add_argument('--step_size', default = 20, type = str)
parser.add_argument('--cachedState', default = ' ', type = str)

args = parser.parse_args()
filename = args.filename
inf_seed = args.inf_seed
gen_seed = args.gen_seed
num_transitions = args.num_transitions
N_GRID = args.N_GRID
max_rows = args.max_rows
numDraws = args.numDraws
numChains = args.numChains
step_size = args.step_size
cachedState = args.cachedState

engine = ccc.get_CrossCatClient('hadoop', seed = inf_seed)

# For Kiva Full Table
# cctypes = ['continuous', 'multinomial', 'continuous', 'continuous', 'multinomial', 
#            'multinomial', 'multinomial', 'multinomial', 'continuous', 'continuous', 
#            'multinomial', 'continuous', 'continuous', 'multinomial', 'continuous', 
#            'continuous', 'continuous', 'continuous', 'multinomial', 'multinomial', 
#            'multinomial', 'continuous', 'multinomial', 'multinomial', 'multinomial', 
#            'continuous', 'continuous', 'multinomial', 'continuous', 'continuous', 
#            'continuous', 'continuous', 'continuous', 'multinomial', 'multinomial', 
#            'continuous', 'multinomial', 'continuous', 'continuous', 'continuous', 
#            'multinomial', 'multinomial', 'multinomial', 'multinomial', 'multinomial', 
#            'multinomial', 'multinomial']

# For Kiva Team Table
# cctypes = ['continuous','multinomial','multinomial','continuous','multinomial',
#            'continuous','continuous','continuous']

# Load the data from table and sub-sample entities to max_rows
T, M_r, M_c = du.read_model_data_from_csv(filename, max_rows, gen_seed,cctypes = cctypes)
T_array = numpy.asarray(T)
num_rows = len(T)
num_cols = len(T[0])
col_names = numpy.array([M_c['idx_to_name'][str(col_idx)] for col_idx in range(num_cols)])
filebase = 'end2end_result'
dataplot_filename = '{!s}_data'.format(filebase)
pu.plot_T(T_array, M_c, filename = dataplot_filename)
for colindx in range(len(col_names)):
    print 'Attribute: {0:30}   Model:{1}'.format(col_names[colindx],M_c['column_metadata'][colindx]['modeltype'])

# First check if we are working from a cached latent state or we need to run the Markov chain
if cachedState == ' ':
    print 'Initializing ...'
    # Call Initialize and Analyze
    X_L_list, X_D_list = engine.initialize(M_c, M_r, T, n_chains = numChains)
    completed_transitions = 0
    n_steps = min(step_size, num_transitions)
    print 'Analyzing ...'
    while (completed_transitions < num_transitions):
        X_L_list, X_D_list = engine.analyze(M_c, T, X_L_list, X_D_list, kernel_list=(),
                                            n_steps=n_steps)
        completed_transitions = completed_transitions+step_size
        print completed_transitions
        saved_dict = {'T':T, 'M_c':M_c, 'X_L_list':X_L_list, 'X_D_list': X_D_list}
        pkl_filename = 'end2end_model_{!s}.pkl.gz'.format(str(completed_transitions))
        f_utils.pickle(saved_dict, filename = pkl_filename)
    
    saved_dict = {'T':T, 'M_c':M_c, 'X_L_list':X_L_list, 'X_D_list': X_D_list}
    pkl_filename = 'end2end_model_{!s}.pkl.gz'.format('last')
    f_utils.pickle(saved_dict, filename = pkl_filename)
else:
    load_dict = f_utils.unpickle(filename = cachedState)
    X_L_list = load_dict['X_L_list']
    X_D_list = load_dict['X_D_list']
    T = load_dict['T']
    M_c = load_dict['M_c']

# Construct and plot column dependency matrix
zplot_filename = '{!s}_feature_z'.format(filebase)
pu.do_gen_feature_z(X_L_list, X_D_list, M_c, zplot_filename, filename)

# Visualize clusters in one sample (the first out of numChains samples) drawn from the posterior
viewplot_filename = '{!s}_view'.format(filebase)
pu.plot_views(T_array, X_D_list[0], X_L_list[0], M_c, filename= viewplot_filename)

# If there are any missing values in the table, fill them in
#T_imputed = uc_utils.impute_table(T, M_c, X_L_list, X_D_list, numDraws, engine.get_next_seed)

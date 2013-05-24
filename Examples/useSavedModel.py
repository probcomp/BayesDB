# Loading a saved model for further analysis
import tabular_predDB.python_utils.file_utils as fu
# 1. Load saved state
load_dict = fu.unpickle(filename = pkl_filename)
X_L_list = load_dict['X_L_list']
X_D_list = load_dict['X_D_list']
T = load_dict['T']
M_c = load_dict['M_c']

# 2. Create and visualize column dependency matrix
zplot_filename = '{!s}_feature_z_pre'.format(filebase)
tmp_utils.do_gen_feature_z(X_L_list, X_D_list, M_c, zplot_filename, filename)

# 3. Continue transitioning the Markov Chain 
X_L_list_new = []
X_D_list_new = []
num_transitions = 10

for chain_idx in range(numChains):
    print 'Chain {!s}'.format(chain_idx)
    X_L_in = X_L_list[chain_idx]
    X_D_in = X_D_list[chain_idx]
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L_in, X_D_in, kernel_list=(),
                                          n_steps=num_transitions)
    X_L_list_new.append(X_L_prime)
    X_D_list_new.append(X_D_prime)

# 4. Create and visualize column dependency matrix again
zplot_filename = '{!s}_feature_z_post'.format(filebase)
tmp_utils.do_gen_feature_z(X_L_list_new, X_D_list_new, M_c, zplot_filename, filename)

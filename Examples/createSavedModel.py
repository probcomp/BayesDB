# Creating a model and saving the state

# 1. Import packages/modules needed
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.data_utils as du
from tabular_predDB.jsonrpc_http.Engine import Engine

# 2. Load a data table from csv file. In this example, we use synthetic data
filename = 'flight_data_subset_missing_data.csv'
T, M_r, M_c = du.read_model_data_from_csv(filename, gen_seed=0)

# 3. Initialize CrossCat Engine and Build Model
engine = Engine(seed=0)
X_L_list = []
X_D_list = []
numChains = 10
num_transitions = 10

for chain_idx in range(numChains):
    print 'Chain {!s}'.format(chain_idx)
    M_c_prime, M_r_prime, X_L, X_D = engine.initialize(M_c, M_r, T)
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=(),
                                          n_steps=num_transitions)
    X_L_list.append(X_L_prime)
    X_D_list.append(X_D_prime)

saved_dict = {'T':T, 'M_c':M_c, 'X_L_list':X_L_list, 'X_D_list': X_D_list}
pkl_filename = 'flight_data_saved_model.pkl.gz'
fu.pickle(saved_dict, filename = pkl_filename)

# Using CrossCat to Examine Column Dependencies
# 1. Import packages/modules needed
import numpy
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import CrossCatClient as ccc
import useCase_utils as uc_utils


# 2. Load a data table from csv file. In this example, we use synthetic data
filename = 'flight_data_subset_missing_data.csv'
filebase = 'flight_data_subset_missing_data'
T, M_r, M_c = du.read_model_data_from_csv(filename, gen_seed=0)
T_array = numpy.asarray(T)
num_rows = len(T)
num_cols = len(T[0])
col_names = numpy.array([M_c['idx_to_name'][str(col_idx)] for col_idx in range(num_cols)])
dataplot_filename = '{!s}_data'.format(filebase)
pu.plot_T(T_array, M_c, filename = dataplot_filename)

for colindx in range(len(col_names)):
    print 'Attribute: {0:30}   Model:{1}'.format(col_names[colindx],M_c['column_metadata'][colindx]['modeltype'])


# 3. Initialize CrossCat Engine and Build Model
engine = ccc.get_CrossCatClient('local', seed = 0)
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

# 4. Impute all missing values (nan's) in the table
numDraws = 10; # The number of draws from the distribution computed from each sample
T_imputed = uc_utils.impute_table(T, M_c, X_L_list, X_D_list, numDraws, engine.get_next_seed)

#5. Write the new table to a csv file
imputed_file = '{!s}_imputed.csv'.format(filebase)
du.write_csv(imputed_file, T_imputed, col_names.tolist())

# Using CrossCat to Examine Column Dependencies
# 1. Import packages/modules needed
import numpy, csv,  tmp_utils, pylab
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
from tabular_predDB.jsonrpc_http.Engine import Engine

# 2. Load a data table from csv file. In this example, we use synthetic data
filename = 'flight_data_subset_missing_data.csv'
filebase = 'flight_data_subset_missing_data'
T, M_r, M_c = du.read_model_data_from_csv(filename, gen_seed=0)
T = numpy.asarray(T)
num_rows = len(T)
num_cols = len(T[0])
col_names = numpy.array([M_c['idx_to_name'][str(col_idx)] for col_idx in range(num_cols)])
dataplot_filename = '{!s}_data'.format(filebase)
tmp_utils.plot_T(T, M_c, filename = dataplot_filename)

coltype = []
for colindx in range(len(col_names)):
    print 'Attribute: {!s}   Model:{!s}'.format(col_names[colindx],M_c['column_metadata'][colindx]['modeltype'])
    if M_c['column_metadata'][colindx]['modeltype'] == 'normal_inverse_gamma':
        coltype.append('continuous')
    else:
        coltype.append('multinomial')

# 3. Initialize CrossCat Engine and Build Model
engine = Engine( )
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

# 4. Find indices of missing data
missingRowIndices = [missingRowIndices for missingRowIndices in range(len(T)) if any(numpy.isnan(T[missingRowIndices]))]

missingColIndices = []
for x in missingRowIndices:
    y = [y for y in range(len(T[0])) if numpy.isnan(T[x][y])]
    missingColIndices.append(y[0]) 

# 5. Build queries for imputation
numImputations = len(missingRowIndices)
Q = []
for i in range(numImputations):
    print missingRowIndices[i],missingColIndices[i], len(T), len(T[0])
    Q.append([missingRowIndices[i],missingColIndices[i]])

#6. Impute missing values in table
numDraws = 10; # The number of draws from the distribution computed from each sample
samples_list = []
values_list = []
for queryindx in range(len(Q)):
    values, samples = engine.impute(M_c, X_L_list, X_D_list, [], [Q[queryindx]], numDraws,return_samples_flag = True)
    values_list.append(values)
    samples_list.append(samples)

#7. Put the samples back into the data table
T_imputed = T
for imputeindx in range(numImputations):
    if coltype[missingColIndices[imputeindx]] == 'continuous':
        T_imputed[missingRowIndices[imputeindx]][missingColIndices[imputeindx]] = values_list[imputeindx]
    else:
        T_imputed[missingRowIndices[imputeindx]][missingColIndices[imputeindx]] = M_c['column_metadata'][missingColIndices[imputeindx]]['value_to_code'][values_list[imputeindx]]

#8. Write the new table to a csv file
imputed_file = '{!s}_imputed.csv'.format(filebase)
tmp_utils.write_csv(imputed_file, T, col_names.tolist())

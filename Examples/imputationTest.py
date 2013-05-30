# Using CrossCat to Examine Column Dependencies
# 1. Import packages/modules needed
import numpy, os
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.CrossCatClient as ccc
import tabular_predDB.python_utils.useCase_utils as uc_utils

# 2. Load a data table from csv file. In this example, we use synthetic data
filename = 'flight_data_subset.csv'
filebase = 'flight_data_subset'
T, M_r, M_c = du.read_model_data_from_csv(filename, gen_seed=0)
T_array = numpy.asarray(T)
num_rows = len(T)
num_cols = len(T[0])
col_names = numpy.array([M_c['idx_to_name'][str(col_idx)] for col_idx in range(num_cols)])
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

# 4. Create missing cells and store ground truth
# Also create queries 
numImputations = 10
random_state = numpy.random.RandomState(0)
numElements = len(T)*len(T[0]);
missingElementIndices = random_state.permutation(xrange(numElements))[:(numImputations)]
missingRowIndices = numpy.mod(missingElementIndices+1,len(T))
missingColIndices = [(missingElementIndices[indx])/len(T) for indx in range(numImputations)]

TrueVal = numpy.zeros(numImputations)
Q = []
for i in range(numImputations):
    #print missingRowIndices[i],missingColIndices[i], len(T), len(T[0])
    TrueVal[i] = T[missingRowIndices[i]][missingColIndices[i]]
    T[missingRowIndices[i]][missingColIndices[i]] = numpy.NaN
    Q.append([missingRowIndices[i],missingColIndices[i]])

# 5. Impute cells using Cross Cat
crosscat_samples_list = []
crosscat_values_list = []
for queryindx in range(len(Q)):
    crosscat_values, crosscat_samples = su.impute(M_c, X_L_list, X_D_list, [], [Q[queryindx]], 500,engine.get_next_seed, return_samples=True)
    crosscat_samples_list.append(crosscat_samples)
    crosscat_values_list.append(crosscat_values)

# 6. Find baseline imputation values
baseline_samples_list = []
baseline_values_list = []
for queryindx in range(len(Q)):
    modelType = M_c['column_metadata'][missingColIndices[queryindx]]['modeltype']
    imputation_function = su.modeltype_to_imputation_function[modelType]
    baseline_samples = T_array[:,missingColIndices[queryindx]]
    baseline_values = imputation_function(baseline_samples,engine.get_next_seed)
    baseline_samples_list.append(baseline_samples)
    baseline_values_list.append(baseline_values)

# 7. Display results in table
print '{0} {1} {2} {3}'.format('True Value'.center(15), 'Baseline'.center(15), 'CrossCat'.center(15),'Column Name'.ljust(15))
for indx in range(len(Q)):
    #print '{0} {1} {2} {3}'.format(str(TrueVal[indx]).center(15),str(baseline_values_list[indx]).center(15),
    #                               str(crosscat_values_list[indx]).center(15), str(col_names[missingColIndices[indx]]).ljust(15))
    print '{0:>15.2f} {1:>15.2f} {2:>15.2f} {3:<15}'.format(TrueVal[indx],baseline_values_list[indx],crosscat_values_list[indx],col_names[missingColIndices[indx]])

# # 8. Display marginal distribution and overlay ground truth 
# Pick the query number to display comparison for
queryindx = 6


modelType = M_c['column_metadata'][missingColIndices[queryindx]]['modeltype']

plot_lims = pu.plot_predicted_value(crosscat_values_list[queryindx], crosscat_samples_list[queryindx], modelType, filename = 'crosscat_imputation.png', plotcolor='red',truth=TrueVal[queryindx])

pu.plot_predicted_value(baseline_values_list[queryindx], baseline_samples_list[queryindx], modelType, filename = 'baseline_imputation.png', plotcolor='blue',truth=TrueVal[queryindx], x_axis_lim = plot_lims)

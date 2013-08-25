# Using CrossCat to Examine Column Dependencies
# 1. Import packages/modules needed
import numpy
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

# 3. Split the data table into a training and test set
T_train = T_array[0:(num_rows/2 - 1)]
T_test =  T_array[num_rows/2 : num_rows]

# 4. Initialize CrossCat Engine and Build Model using only the training data
engine = ccc.get_CrossCatClient('local', seed = 0)
X_L_list = []
X_D_list = []
numChains = 10
num_transitions = 10

for chain_idx in range(numChains):
    print 'Chain {!s}'.format(chain_idx)
    X_L, X_D = engine.initialize(M_c, M_r, T_train)
    X_L_prime, X_D_prime = engine.analyze(M_c, T_train, X_L, X_D, kernel_list=(),
                                          n_steps=num_transitions)
    X_L_list.append(X_L_prime)
    X_D_list.append(X_D_prime)

# 5. Select a single row from the test sets and delete the information in three (arbitrarily chosen) columns and predict the deleted cells using the CrossCat model and the rest of the information in the row
test_row = []
test_row.append(T_test[0])
missing_fields = [0, 4, 9]
condition_fields = [colindx for colindx in range(num_cols) if colindx not in missing_fields]
Q = []
Y = []

numDraws = 500
predicted_values = []
# Construct the query 2-tuples [row, column] & condition 3-tuples [row, column, value]
for indx_row in range(len(test_row)):
    for indx_col in range(len(missing_fields)):
        Q = [len(T_train)+indx_row, missing_fields[indx_col]]
        Y = []
        for indx_col in range(len(condition_fields)):
            Y.append([len(T_train)+indx_row+1, condition_fields[indx_col], test_row[indx_row][condition_fields[indx_col]]])

        value = uc_utils.predict(M_c, X_L_list, X_D_list, Y, [Q], numDraws, engine.get_next_seed)
        predicted_values.append(value)


print predicted_values

# 6. Predict in table
test_rows = (T_test[0:3,:])
missing_fields = [0, 4, 9]
test_rows[:,missing_fields] = numpy.nan
print test_rows
T_predicted = uc_utils.predict_in_table(test_rows, T, M_c, X_L, X_D, numDraws, engine.get_next_seed)

import numpy, pylab, os, pdb, csv
import tabular_predDB.python_utils.sample_utils as su


def impute_table(T, M_c, X_L_list, X_D_list, numDraws, get_next_seed):

    num_rows = len(T)
    num_cols = len(T[0])
    # Identify column types
    col_names = numpy.array([M_c['idx_to_name'][str(col_idx)] for col_idx in range(num_cols)])
    coltype = []
    for colindx in range(len(col_names)):
        if M_c['column_metadata'][colindx]['modeltype'] == 'normal_inverse_gamma':
            coltype.append('continuous')
        else:
            coltype.append('multinomial')

    # FIXME: This code currently works if there is one missing value in a table
    #        Predict table below implements this correctly        

    # Find missing values            
    missingRowIndices = [missingRowIndices for missingRowIndices in range(len(T)) if any(numpy.isnan(T[missingRowIndices]))]
    missingColIndices = []
    for x in missingRowIndices:
        y = [y for y in range(len(T[0])) if numpy.isnan(T[x][y])]
        missingColIndices.append(y[0]) 

    # Build queries for imputation
    numImputations = len(missingRowIndices)
    Q = []
    for i in range(numImputations):
        #print missingRowIndices[i],missingColIndices[i], len(T), len(T[0])
        Q.append([missingRowIndices[i],missingColIndices[i]])

    # Impute missing values in table
    values_list = []
    for queryindx in range(len(Q)):
        values = su.impute(M_c, X_L_list, X_D_list, [], [Q[queryindx]], numDraws, get_next_seed)
        values_list.append(values)

    # Put the samples back into the data table
    T_imputed = T
   
    for imputeindx in range(numImputations):
        T_imputed[missingRowIndices[imputeindx]][missingColIndices[imputeindx]] = values_list[imputeindx]
    for colindx in range(len(T[0])):
        if coltype[colindx] == 'multinomial':
            for rowindx in range(len(T)):
                T_imputed[rowindx][colindx] =  M_c['column_metadata'][colindx]['value_to_code'][T_imputed[rowindx][colindx]]

    return T_imputed

def predict(M_c, X_L, X_D, Y, Q, n, get_next_seed):
    # Predict is currently the same as impute except that the row Id in the query must lie outside the 
    # length of the table used to generate the model
    # For now, we will just call "impute" and leave it to the user to generate the query correctly 
    
    # FIXME: allow more than one cell to be predicted
    assert(len(Q)==1)
    e, samples = su.impute(M_c, X_L, X_D, Y, Q, n, get_next_seed)
    return e

def predict_and_confidence(M_c, X_L, X_D, Y, Q, n, get_next_seed):
    # FIXME: allow more than one cell to be predicted
    assert(len(Q)==1)
    e, confidence = su.impute_and_confidence(M_c, X_L, X_D, Y, Q, n, get_next_seed)
    return e, confidence
    
def predict_in_table(T_test, T, M_c, X_L, X_D, numDraws, get_next_seed):
    # Predict all missing values in a table
    num_rows = len(T)
    num_cols = len(T[0])
    num_rows_test= len(T)
    num_cols_test = len(T[0])

    assert(num_cols == num_cols_test)
    
    # Identify column types
    col_names = numpy.array([M_c['idx_to_name'][str(col_idx)] for col_idx in range(num_cols)])
    coltype = []
    for colindx in range(len(col_names)):
        print 'Attribute: {!s}   Model:{!s}'.format(col_names[colindx],M_c['column_metadata'][colindx]['modeltype'])
        if M_c['column_metadata'][colindx]['modeltype'] == 'normal_inverse_gamma':
            coltype.append('continuous')
        else:
            coltype.append('multinomial')

    # Find missing values            
    rowsWithNans = [rowsWithNans for rowsWithNans in range(len(T_test)) if any(numpy.isnan(T_test[rowsWithNans]))]
    Q = []
    for x in rowsWithNans:
        y = [y for y in range(len(T_test[0])) if numpy.isnan(T_test[x][y])]
        Q.extend(zip([x]*len(y), y)) 

    # Build queries for imputation
    numPredictions = len(Q)
 
    # Impute missing values in table
    values_list = []
    for queryindx in range(len(Q)):
        # Build conditions - we have to loop over conditions because "Impute" can only handles one query at a time
        # We already know the row Id, so just build conditions based on the rest of the row if data is available
        # Find attributes in the row that are available
        indx_row = Q[queryindx][0]
        condition_fields = numpy.where(~numpy.isnan(T_test[indx_row]))
        Y = []
        for indx_col in range(len(condition_fields[0])):
            Y.append([num_rows+indx_row, condition_fields[0][indx_col], T_test[indx_row][condition_fields[0][indx_col]]])
        print [Q[queryindx]], Y
       
        values = predict(M_c, X_L, X_D, Y, [Q[queryindx]], numDraws, get_next_seed)
        values_list.append(values)

    # Put the samples back into the data table
    T_predicted = T_test

    for predictindx in range(numPredictions):
        predicted_value = values_list[predictindx]
        if coltype[Q[predictindx][1]] == 'multinomial':
            predicted_value = M_c['column_metadata'][Q[predictindx][1]]['value_to_code'][predicted_value]
        T_predicted[Q[predictindx][0]][Q[predictindx][1]] = values_list[predictindx]

    return T_predicted


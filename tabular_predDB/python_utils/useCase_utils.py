import numpy, pylab, os, csv
import tabular_predDB.python_utils.sample_utils as su
from copy import copy

def isnan_mixedtype(input_list):
    # Checks to see which elements are nans in a list of characters and numbers (the characters cannot be nans)
    outlist = numpy.zeros(len(input_list))

    num_indices = [x for x in range(len(input_list)) if numpy.isreal(input_list[x]) and numpy.isnan(input_list[x])]
    outlist[num_indices] = 1
    return outlist

def impute_table(T, M_c, X_L_list, X_D_list, numDraws, get_next_seed):
    T_imputed = copy(T)
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

    rowsWithNans = [i for i in range(len(T)) if any(isnan_mixedtype(T[i]))]
    print rowsWithNans
    Q = []
    for x in rowsWithNans:
        y = [y for y in range(len(T[0])) if isnan_mixedtype([T[x][y]])]
        Q.extend(zip([x]*len(y), y)) 

    numImputations = len(Q)
    # Impute missing values in table
    values_list = []
    for queryindx in range(len(Q)):
        values = su.impute(M_c, X_L_list, X_D_list, [], [Q[queryindx]], numDraws, get_next_seed)
        values_list.append(values)

    
    # Put the samples back into the data table
    for imputeindx in range(numImputations):
        imputed_value = values_list[imputeindx]
        if coltype[Q[imputeindx][1]] == 'multinomial':
            imputed_value = M_c['column_metadata'][Q[imputeindx][1]]['value_to_code'][imputed_value]
        T_imputed[Q[imputeindx][0]][Q[imputeindx][1]] = imputed_value

    return T_imputed

def predict(M_c, X_L, X_D, Y, Q, n, get_next_seed, return_samples=False):
    # Predict is currently the same as impute except that the row Id in the query must lie outside the 
    # length of the table used to generate the model
    # For now, we will just call "impute" and leave it to the user to generate the query correctly 
    
    # FIXME: allow more than one cell to be predicted
    assert(len(Q)==1)
    if return_samples:
        e, samples = su.impute(M_c, X_L, X_D, Y, Q, n, get_next_seed, return_samples=True)
    else:
        e = su.impute(M_c, X_L, X_D, Y, Q, n, get_next_seed)
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
        if M_c['column_metadata'][colindx]['modeltype'] == 'normal_inverse_gamma':
            coltype.append('continuous')
        else:
            coltype.append('multinomial')

    # Find missing values            
    rowsWithNans = [rowsWithNans for rowsWithNans in range(len(T_test)) if any(isnan_mixedtype(T_test[rowsWithNans]))]
    Q = []
    for x in rowsWithNans:
        y = [y for y in range(len(T_test[0])) if isnan_mixedtype([T_test[x][y]])]
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
        #print [Q[queryindx]], Y
       
        values = predict(M_c, X_L, X_D, Y, [Q[queryindx]], numDraws, get_next_seed)
        values_list.append(values)

    # Put the samples back into the data table
    T_predicted = copy(T_test)

    for predictindx in range(numPredictions):
        predicted_value = values_list[predictindx]
        if coltype[Q[predictindx][1]] == 'multinomial':
            predicted_value = M_c['column_metadata'][Q[predictindx][1]]['value_to_code'][predicted_value]
        T_predicted[Q[predictindx][0]][Q[predictindx][1]] = predicted_value

    return T_predicted

def row_similarity(row_index, column_indices, X_D_list, X_L_list, num_returns = 10):

    # Finds rows most similar to row_index (index into the table) conditioned on
    # attributes represented by the column_indices based on the mappings into
    # categories, X_D_list, generated in each chain.

    # Create a list of scores for each row in the table
    score = numpy.zeros(len(X_D_list[0][0]))

    # For one chain
    for chain_indx in range(len(X_D_list)):
        X_D = X_D_list[chain_indx]
        X_L = X_L_list[chain_indx]

        # Find the number of views and view assignments from X_L
        view_assignments = X_L['column_partition']['assignments']
        view_assignments = numpy.array(view_assignments)
        num_features = len(view_assignments) # i.e, number of attributes
        num_views = len(set(view_assignments))

        # Find which view each conditional attribute (column_indices) belongs to 
        views_for_cols = view_assignments[column_indices]
        print views_for_cols
        for viewindx in views_for_cols:
            # Find which cluster the target row is in 
            tgt_cluster = X_D[viewindx][row_index]
    
            # Find every row in this cluster and give them all a point
            match_rows = [i for i in range(len(X_D[viewindx])) if X_D[viewindx][i] == tgt_cluster]
            score[match_rows] = score[match_rows] + 1
            
    
    # Normalize between 0 and 1
    normfactor = len(column_indices)*len(X_D_list)
    normscore = numpy.asarray([float(a)/normfactor for a in score])

    # Sort in descending order
    argsorted = numpy.argsort(normscore)[::-1]     
    sortedscore = normscore[argsorted]

    return argsorted[0:num_returns], sortedscore[0:num_returns]

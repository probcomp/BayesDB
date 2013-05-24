import numpy, hcluster, pylab, os, pdb, csv
from collections import Counter
import tabular_predDB.python_utils.sample_utils as su

def do_gen_feature_z(X_L_list, X_D_list, M_c, filename, tablename=''):
    num_cols = len(X_L_list[0]['column_partition']['assignments'])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)
    # extract unordered z_matrix
    num_latent_states = len(X_L_list)
    z_matrix = numpy.zeros((num_cols, num_cols))
    for X_L in X_L_list:
      assignments = X_L['column_partition']['assignments']
      for i in range(num_cols):
        for j in range(num_cols):
          if assignments[i] == assignments[j]:
            z_matrix[i, j] += 1
    z_matrix /= float(num_latent_states)
    # hierachically cluster z_matrix
    Y = hcluster.pdist(z_matrix)
    Z = hcluster.linkage(Y)
    pylab.figure()
    hcluster.dendrogram(Z)
    intify = lambda x: int(x.get_text())
    reorder_indices = map(intify, pylab.gca().get_xticklabels())
    pylab.close()
    # REORDER! 
    z_matrix_reordered = z_matrix[:, reorder_indices][reorder_indices, :]
    column_names_reordered = column_names[reorder_indices]
    # actually create figure
    fig = pylab.figure()
    fig.set_size_inches(16, 12)
    pylab.imshow(z_matrix_reordered, interpolation='none',
                 cmap=pylab.matplotlib.cm.Greens)
    pylab.colorbar()
    if num_cols < 14:
      pylab.gca().set_yticks(range(num_cols))
      pylab.gca().set_yticklabels(column_names_reordered, size='x-small')
      pylab.gca().set_xticks(range(num_cols))
      pylab.gca().set_xticklabels(column_names_reordered, rotation=90, size='x-small')
    else:
      pylab.gca().set_yticks(range(num_cols)[::2])
      pylab.gca().set_yticklabels(column_names_reordered[::2], size='x-small')
      pylab.gca().set_xticks(range(num_cols)[1::2])
      pylab.gca().set_xticklabels(column_names_reordered[1::2],
                                  rotation=90, size='small')
    pylab.title('column dependencies for: %s' % tablename)
    pylab.savefig(filename)

def get_aspect_ratio(T_array):
    num_rows = len(T_array)
    num_cols = len(T_array[0])
    aspect_ratio = float(num_cols)/num_rows
    return aspect_ratio

def my_savefig(filename, dir='', close=True):
    if filename is not None:
        full_filename = os.path.join(dir, filename)
        pylab.savefig(full_filename)
        if close:
            pylab.close()

def plot_T(T_array, M_c, filename=None, dir='', close=True):
    num_cols = len(T_array[0])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)

    aspect_ratio = get_aspect_ratio(T_array)
    pylab.figure()
    pylab.imshow(T_array, aspect=aspect_ratio, interpolation='none',
                 cmap=pylab.matplotlib.cm.Greens)
    pylab.gca().set_xticks(range(num_cols))
    pylab.gca().set_xticklabels(column_names, rotation=90, size='x-small')

    pylab.show()
    
    my_savefig(filename, dir, close)

def plot_views(T_array, X_D, X_L, M_c, filename=None, dir='', close=True):

    num_cols = len(X_L['column_partition']['assignments'])
    column_names = [M_c['idx_to_name'][str(idx)] for idx in range(num_cols)]
    column_names = numpy.array(column_names)

    fig = pylab.figure()
    view_assignments = X_L['column_partition']['assignments']
    view_assignments = numpy.array(view_assignments)
    num_features = len(view_assignments)
    num_views = len(set(view_assignments))
    
    disLeft = 0.1
    disRight = 0.1
    viewSpacing = 0.1/(max(2,num_views)-1)
    nxtAxDisLeft = disLeft
    axpos2 = 0.2
    axpos4 = 0.75
    
    for view_idx in range(num_views):
        X_D_i = X_D[view_idx]
        argsorted = numpy.argsort(X_D_i)
        is_this_view = view_assignments==view_idx
        xticklabels = numpy.nonzero(is_this_view)[0]
        num_cols_i = sum(is_this_view)
        T_array_sub = T_array[:,is_this_view][argsorted]
        nxtAxWidth = (float(num_cols_i)/num_features)*(1-viewSpacing*(num_views-1.)-disLeft-disRight)
        axes_pos = nxtAxDisLeft, axpos2, nxtAxWidth, axpos4
        currax = fig.add_axes(axes_pos)
        nxtAxDisLeft = nxtAxDisLeft+nxtAxWidth+viewSpacing
        aspect_ratio = get_aspect_ratio(T_array)
        
        # Normalize each column to display
        mincols = T_array_sub.min(axis=0)
        maxcols = T_array_sub.max(axis=0)
        T_norm = (T_array_sub-mincols[numpy.newaxis,:])/(maxcols[numpy.newaxis,:]-mincols[numpy.newaxis,:])
        pylab.imshow(T_norm, aspect = 'auto',
                     interpolation='none',cmap=pylab.matplotlib.cm.Greens)
        old_tmp = 0
        
        for y in range(max(X_D_i)):
            tmp = numpy.sum([X_D_i[x] == y for x in range(len(X_D_i))])
            if tmp > 5:
                pylab.plot(numpy.arange(num_cols_i+1)-0.5, [old_tmp+tmp]*(num_cols_i+1),color='red',linewidth=2,hold='true')
            old_tmp = old_tmp+tmp
               
        pylab.gca().set_xticks(range(num_cols_i))
        #pylab.gca().set_xticklabels(map(str, xticklabels))
        #pdb.set_trace()
        pylab.gca().set_xticklabels(column_names[is_this_view], rotation=90, size='x-small')
        pylab.gca().set_yticklabels([])
        pylab.xlim([-0.5, num_cols_i-0.5])
        pylab.ylim([0, len(T_array_sub)])

        pylab.show()
        if view_idx!=0: pylab.gca().set_yticklabels([])
    my_savefig(filename, dir, close)

def plotImputedValue(value, samples, modelType, filename='imputed_value_hist.png', plotcolor='red', truth=None, x_axis_lim=None):

    fig = pylab.figure()
    # Find 50% bounds
    curr_std = numpy.std(samples)
    curr_delta = 2*curr_std/100;
    ndraws = len(samples)
    
    for thresh in numpy.arange(curr_delta, 2*curr_std, curr_delta):
        withinbounds = len([i for i in range(len(samples)) if samples[i] < (value+thresh) and samples[i] > (value-thresh)])
        if float(withinbounds)/ndraws > 0.5:
            break

    bounds = [value-thresh, value+thresh]
    
    # Plot histogram
    # 'normal_inverse_gamma': continuous_imputation,
    # 'symmetric_dirichlet_discrete': multinomial_imputation,
    
    if modelType == 'normal_inverse_gamma':
        nx, xbins, rectangles = pylab.hist(samples,bins=40,normed=0,color=plotcolor)
    elif modelType == 'symmetric_dirichlet_discrete':
        bin_edges = numpy.arange(numpy.min(samples)-0.5, numpy.max(samples)-0.5, 1)  
        nx, xbins, rectangles = pylab.hist(samples,bin_edges,normed=0,color=plotcolor)
    else:
        print 'Unsupported model type'

    pylab.clf()

    nx_frac = nx/float(sum(nx))
    x_width = [(xbins[i+1]-xbins[i]) for i in range(len(xbins)-1)]
    pylab.bar(xbins[0:len(xbins)-1],nx_frac,x_width,color=plotcolor)
    pylab.plot([value, value],[0,1], color=plotcolor, hold=True,linewidth=2)                      
    pylab.plot([bounds[0], bounds[0]],[0,1], color=plotcolor, hold=True, linestyle='--',linewidth=2)
    pylab.plot([bounds[1], bounds[1]],[0,1], color=plotcolor, hold=True, linestyle='--',linewidth=2)
    if truth != None:
        pylab.plot([truth, truth],[0,1], color='green', hold=True, linestyle='--',linewidth=2)
    pylab.show()

    if x_axis_lim != None:
        pylab.xlim(x_axis_lim)
    my_savefig(filename, '', False)
    return pylab.gca().get_xlim()

def write_csv(filename, T, header = None):
    with open(filename,'w') as fh:
        csv_writer = csv.writer(fh, delimiter=',')
        if header != None:
            csv_writer.writerow(header)
        [csv_writer.writerow(T[i]) for i in range(len(T))]


def impute_table(T, M_c, X_L_list, X_D_list, numDraws, get_next_seed):

    num_rows = len(T)
    num_cols = len(T[0])
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
    missingRowIndices = [missingRowIndices for missingRowIndices in range(len(T)) if any(numpy.isnan(T[missingRowIndices]))]
    missingColIndices = []
    for x in missingRowIndices:
        y = [y for y in range(len(T[0])) if numpy.isnan(T[x][y])]
        missingColIndices.append(y[0]) 

    # Build queries for imputation
    numImputations = len(missingRowIndices)
    Q = []
    for i in range(numImputations):
        print missingRowIndices[i],missingColIndices[i], len(T), len(T[0])
        Q.append([missingRowIndices[i],missingColIndices[i]])

    # Impute missing values in table
    samples_list = []
    values_list = []
    for queryindx in range(len(Q)):
        values, samples = su.impute(M_c, X_L_list, X_D_list, [], [Q[queryindx]], numDraws, get_next_seed)
        values_list.append(values)
        samples_list.append(samples)

    # Put the samples back into the data table
    T_imputed = T
   
    # for imputeindx in range(numImputations):
    #     if coltype[missingColIndices[imputeindx]] == 'continuous':
    #         T_imputed[missingRowIndices[imputeindx]][missingColIndices[imputeindx]] = values_list[imputeindx]
    #     else:
    #         T_imputed[missingRowIndices[imputeindx]][missingColIndices[imputeindx]] = M_c['column_metadata'][missingColIndices[imputeindx]]['value_to_code'][values_list[imputeindx]]

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


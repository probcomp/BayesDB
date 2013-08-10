import numpy
from sklearn import metrics


def truth_from_permute_indices(data_inverse_permutation_indices, num_rows,num_cols,num_views, num_clusters):
    # We assume num_rows is divisible by num_clusters and num_cols is divisible by num_views
    num_cols_per_view = num_cols/num_views
    view_assignments = []
    for viewindx in range(num_views):
        view_assignments = view_assignments + [viewindx]*num_cols_per_view

    num_rows_per_cluster = num_rows/num_clusters
    
    reference_list = []
    for clusterindx in range(num_clusters):
        reference_list = reference_list + [clusterindx]*num_rows_per_cluster
        
    X_D_truth = []
    for viewindx in range(num_views):
        X_D_truth.append([a for (b,a) in sorted(zip(data_inverse_permutation_indices[viewindx], reference_list))])
        
        
    return view_assignments, X_D_truth

def ARI_CrossCat(Xc, Xrv, XRc, XRrv):
    ''' Adjusted Rand Index (ARI) calculation for a CrossCat clustered table
    
    To calculate ARI based on the CrossCat partition, each cell in the
    table is considered as an instance to be assigned to a cluster. A cluster
    is defined by both the view index AND the category index. In other words,
    if, and only if, two cells, regardless of which columns and rows they belong
    to, are lumped into the same view and category, the two cells are considered
    to be in the same cluster. 

    For a table of size Nrow x Ncol
    Xc: (1 x Ncol) array of view assignment for each column.
        Note: It is assumed that the view indices are consecutive integers
        starting from 0. Hence, the number of views is equal to highest
        view index plus 1.
    Xrv: (Nrow x Nview) array where each row is the assignmennt of categories for the
        corresponding row in the data table. The i-th element in a row
        corresponds to the category assignment of the i-th view of that row.
    XRc and XRrv have the same format as Xr and Xrv respectively.
    The ARI index is calculated from the comparison of the table clustering
    define by (XRc, XRrv) and (Xc, Xrv).
    '''
    Xrv = Xrv.T
    XRrv = XRrv.T
    # Find the highest category index of all views
    max_cat_index = numpy.max(Xrv)
    # re-assign category indices so that they have different values in
    # different views
    Xrv = Xrv + numpy.arange(0,Xrv.shape[1])*(max_cat_index+1)
    
    # similarly for the reference partition
    max_cat_index = numpy.max(XRrv)
    XRrv = XRrv + numpy.arange(0,XRrv.shape[1])*(max_cat_index+1)
    
    # Table clustering assignment for the first partition
    CellClusterAssgn = numpy.zeros((Xrv.shape[0], Xc.size))
    for icol in range(Xc.size):
        CellClusterAssgn[:,icol]=Xrv[:,Xc[icol]]
    # Flatten the table to a 1-D array compatible with the ARI function 
    CellClusterAssgn = CellClusterAssgn.reshape(CellClusterAssgn.size)
        
    # Table clustering assignment for the second partition
    RefCellClusterAssgn = numpy.zeros((Xrv.shape[0], Xc.size))
    for icol in range(Xc.size):
        RefCellClusterAssgn[:,icol]=XRrv[:,XRc[icol]]
    # Flatten the table
    RefCellClusterAssgn = RefCellClusterAssgn.reshape(RefCellClusterAssgn.size)
        
    # Compare the two partitions using ARI
    ARI = metrics.adjusted_rand_score(RefCellClusterAssgn, CellClusterAssgn)
    ARI_viewonly = metrics.adjusted_rand_score(Xc, XRc)

    return ARI, ARI_viewonly

def multi_chain_ARI(X_L_list, X_D_List, view_assignment_truth, X_D_truth, return_list=False):
    num_chains = len(X_L_list)
    ari_table = numpy.zeros(num_chains)
    ari_views = numpy.zeros(num_chains)
    for chainindx in range(num_chains):
        view_assignments = X_L_list[chainindx]['column_partition']['assignments']
        curr_ari_table, curr_ari_views = ARI_CrossCat(numpy.asarray(view_assignments), numpy.asarray(X_D_List[chainindx]), numpy.asarray(view_assignment_truth), numpy.asarray(X_D_truth))
        ari_table[chainindx] = curr_ari_table
        ari_views[chainindx] = curr_ari_views

    ari_table_mean = numpy.mean(ari_table)
    ari_views_mean = numpy.mean(ari_views)
    if return_list:
        return ari_table, ari_views
    else:
        return ari_table_mean, ari_views_mean
    

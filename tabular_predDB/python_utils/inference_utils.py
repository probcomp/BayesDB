import sys
import copy
from collections import Counter

from scipy.misc import logsumexp
import numpy
import random
import math

import tabular_predDB.cython_code.ContinuousComponentModel as CCM
import tabular_predDB.cython_code.MultinomialComponentModel as MCM
import tabular_predDB.python_utils.sample_utils as su

import pdb


def mutual_information_to_linfoot(MI):
    return (1-math.exp(-2*MI))**0.5

# return the estimated mutual information for each pair of columns on Q given
# the set of samples in X_Ls and X_Ds. Q is a list of tuples where each tuple
# contains X and Y, the columns to compare. 
# Q = [(X_1, Y_1), (X_2, Y_2), ..., (X_n, Y_n)]
# Returns a list of list where each sublist is a set of MI's and Linfoots from
# each crosscat posterior sample. 
# See tests/test_mutual_information.py and 
# tests/test_mutual_information_vs_correlation.py for useage examples
def mutual_information(M_c, X_Ls, X_Ds, Q, n_samples=1000):
    #
    assert(len(X_Ds) == len(X_Ls))
    n_postertior_samples = len(X_Ds)

    n_rows = len(X_Ds[0][0])
    n_cols = len(M_c['column_metadata'])

    MI = []
    Linfoot = []

    get_next_seed = lambda: random.randrange(32767)

    for query in Q:
        assert(len(query) == 2)
        assert(query[0] >= 0 and query[0] < n_cols)
        assert(query[1] >= 0 and query[1] < n_cols)

        X = query[0]
        Y = query[1]

        MI_sample = []
        Linfoot_sample = []
        for sample in range(n_postertior_samples):
            
            X_L = X_Ls[sample]
            X_D = X_Ds[sample]

            MI_s = estimiate_MI_sample(X, Y, M_c, X_L, X_D, get_next_seed, n_samples=n_samples)

            linfoot = mutual_information_to_linfoot(MI_s)
            if not linfoot >= 0 or not linfoot <= 1:
                pdb.set_trace()

            MI_sample.append(MI_s)

            Linfoot_sample.append(linfoot)

        MI.append(MI_sample)
        Linfoot.append(Linfoot_sample)

         
    assert(len(MI) == len(Q))
    assert(len(Linfoot) == len(Q))

    return MI, Linfoot

# estimates the mutual information part for columns X and Y on row.
def estimiate_MI_sample(X, Y, M_c, X_L, X_D, get_next_seed, n_samples=1000):

    
    get_view_index = lambda which_column: X_L['column_partition']['assignments'][which_column]
    # get_cluster_index = lambda which_view, which_row : X_D[which_view][which_row]

    view_X = get_view_index(X)
    view_Y = get_view_index(Y)

    # independent
    if view_X != view_Y:
        return 0

    # get cluster log_ps only for existing clusters
    view_state = X_L['view_state'][view_X]
    cluster_logps = su.determine_cluster_crp_logps(view_state)
    cluster_crps = numpy.exp(cluster_logps)
    n_clusters = len(cluster_crps)

    # get components models for each cluster for X and Y
    component_models_X = [0]*n_clusters
    component_models_Y = [0]*n_clusters
    for i in range(n_clusters):
        cluster_models = su.create_cluster_model_from_X_L(M_c, X_L, view_X, i)
        component_models_X[i] = cluster_models[X]
        component_models_Y[i] = cluster_models[Y]

    MI = 0
    for i in range(n_samples):
        # draw a cluster 
        cluster_idx = numpy.nonzero(numpy.random.multinomial(1, cluster_crps))[0][0]

        x = component_models_X[cluster_idx].get_draw(get_next_seed())
        y = component_models_Y[cluster_idx].get_draw(get_next_seed())

        # calculate marginal logs
        Pxy = numpy.zeros(n_clusters)
        Px = numpy.zeros(n_clusters)
        Py = numpy.zeros(n_clusters)

        for j in range(n_clusters):
            Px[j] = component_models_X[j].calc_element_predictive_logp(x)
            Py[j] = component_models_Y[j].calc_element_predictive_logp(y)
            Pxy[j] = Px[j] + Py[j] + cluster_logps[j]
            Px[j] += cluster_logps[j]
            Py[j] += cluster_logps[j]
        
        Px = logsumexp(Px)
        Py = logsumexp(Py)
        Pxy = logsumexp(Pxy)

        MI += Pxy - Px - Py


    MI /= n_samples

    # ignore MI < 0
    if MI <= 0:
        MI = 0
        
    return MI
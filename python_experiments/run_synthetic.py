import numpy as np
from crosscat_helper import *
from synthetic_helper import *

data_offset = 0
data_reps = 3
hist_reps = 1#10
n_pred_samples = '1'#'250'
n_mcmc_iter = '1'#'500'

for i in range(data_offset, data_offset + data_reps):

    run_ring(i)
    run_correlation(i)
    run_outliers(i)
    run_outliers_correlated(i)
    #run_correlated_pairs(i)
    run_correlated_halves(i)


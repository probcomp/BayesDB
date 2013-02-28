import numpy as np
from synthetic_helper import *

data_offset = 0
data_reps = 1
hist_reps = 1#10
n_pred_samples = '1'#'250'
n_mcmc_iter = '1'#'500'

e = Experiment(
               hist_reps,
               n_pred_samples,
               n_mcmc_iter,
               )

for i in range(data_offset, data_offset + data_reps):

    e.run_ring(i)
#    e.run_correlation(i)
#    e.run_outliers(i)
#    e.run_outliers_correlated(i)
    #e.run_correlated_pairs(i)
#    e.run_correlated_halves(i)


import numpy as np
from synthetic_helper import *

data_offset = 3
data_reps = 2
hist_reps = 10#10
n_pred_samples = '250'#'250'
n_mcmc_iter = '500'#'500'

e = Experiment(
               hist_reps,
               n_pred_samples,
               n_mcmc_iter,
               )

for i in range(data_offset, data_offset + data_reps):

    e.run_ring(i)
    e.run_correlation(i)
    e.run_outliers(i)
    e.run_outliers_correlated(i)
    #e.run_correlated_halves(i)
    #e.run_correlated_pairs(i)


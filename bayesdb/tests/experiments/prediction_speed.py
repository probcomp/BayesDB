#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import matplotlib
matplotlib.use('Agg')

import sys
sys.path.insert(1, '/home/local_jay/BayesDB')

from bayesdb.client import Client
import experiment_utils as eu
import random
import numpy
import pylab
import time
import os
import sklearn.linear_model

def run_experiment(argin):
    bins            = argin["bins"]
    num_iters       = argin["num_iters"]
    num_chains      = argin["num_chains"]
    num_rows        = argin["num_rows"]
    num_cols        = argin["num_cols"]
    num_views       = argin["num_views"]
    num_clusters    = argin["num_clusters"]
    prop_missing    = argin["prop_missing"]
    target_prop_missing = argin["target_prop_missing"]
    impute_samples  = argin["impute_samples"]
    separation      = argin["separation"]
    ct_kernel       = argin["ct_kernel"]
    seed            = argin["seed"]
    num_trials      = argin["num_trials"]

    if seed > 0 :
        random.seed(seed)

    filename = "prediction_speed_ofile.csv"
    table_name = 'exp_prediction_speed'

    argin['cctypes'] = ['continuous']*num_cols
    discrim_cctype = dict(types=sklearn.linear_model.LogisticRegression,
                          params=dict(),
                          inputs=range(num_cols-1))
    argin['cctypes'][-1] = discrim_cctype
    full_cctypes = argin['cctypes']

    argin['separation'] = [argin['separation']]*num_views

    eu.gen_data_discriminative(filename, argin, save_csv=True)

    # generate a new csv
    all_filenames = []
    all_indices = []

    prop_missing_by_col = {len(full_cctypes): target_prop_missing}
    for p in prop_missing:
        data_filename, indices, col_names, extra = eu.gen_missing_data_csv(filename,
                                        p, [], True, prop_missing_by_col=prop_missing_by_col)
        all_indices.append(indices)
        all_filenames.append(data_filename)

    # get the starting table so we can calculate errors
    T_array = extra['array_filled']
    num_rows, num_cols = T_array.shape

    # create a client
    client = Client()

    # set up a dict fro the different config data
    result = dict()
    result['cc'] = numpy.zeros(num_trials)
    result['crp'] = numpy.zeros(num_trials)
    result['nb'] = numpy.zeros(num_trials)
    result['rf'] = numpy.zeros(num_trials)
    result['lr'] = numpy.zeros(num_trials)
    result['max_time'] = 0
    result['min_time'] = float('inf')

    # do analyses
    for p in range(len(prop_missing)):

        this_indices = all_indices[p]
        this_filename = all_filenames[p]
        for config in ['rf', 'lr', 'cc', 'crp', 'nb']:
            config_string = eu.config_map[config]
            table = table_name + '_' + config

            # drop old btable, create a new one with the new data and init models
            client('DROP BTABLE %s;' % table, yes=True)
            client('CREATE BTABLE %s FROM %s;' % (table, this_filename))
            if config == 'rf':
                client('UPDATE SCHEMA FOR %s set %s= discriminative type multi-class random forest' % (table, col_names[-1]))
            elif config == 'lr':
                client('UPDATE SCHEMA FOR %s set %s= discriminative type logistic regression' % (table, col_names[-1]))
#            client('SELECT *, %s FROM %s;' % (col_names[-1], table))
            client('INITIALIZE %i MODELS FOR %s %s;' % (num_chains, table, config_string))
            if num_iters > 0:
                client('ANALYZE %s FOR %i ITERATIONS WAIT;' % (table, num_iters) )

            for i in range(num_trials):
                # imput each index in indices and calculate the speed
                #for col in range(0,num_cols):
                for col in [num_cols - 1]: # For now, only do last column
                    col_name = col_names[col]
                    # confidence is set to zero so that a value is always returned
                    start = time.time()
                    out = client('INFER %s CONF %d from %s WITH %i SAMPLES;' % (col_name, 0, table, impute_samples), pretty=False, pandas_output=False )
                    elapsed = time.time() - start
                    if elapsed > result['max_time']:
                        result['max_time'] = elapsed
                    elif elapsed < result['min_time']:
                        result['min_time'] = elapsed
                    result[config][i] = elapsed


    retval = dict()
    retval['min_time'] = result['min_time']
    retval['max_time'] = result['max_time']
    retval['time_naive_bayes_indexer'] = result['nb']
    retval['time_crp_mixture_indexer'] = result['crp']
    retval['time_crosscat_indexer'] = result['cc']
    retval['time_random_forest_indexer'] = result['rf']
    retval['time_logistic_regression_indexer'] = result['lr']
    retval['prop_missing'] = prop_missing
    retval['config'] = argin

    return retval

def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bins', default=100, type=int)
    parser.add_argument('--num_iters', default=0, type=int)
    parser.add_argument('--num_trials', default=20, type=int) # the number of times to re-run infer for each type
    parser.add_argument('--num_chains', default=4, type=int)
    parser.add_argument('--num_rows', default=300, type=int)
    parser.add_argument('--num_cols', default=4, type=int) #8
    parser.add_argument('--num_clusters', default=4, type=int)
    parser.add_argument('--impute_samples', default=50, type=int)  # samples for IMPUTE
    parser.add_argument('--num_views', default=2, type=int) # data generation
    parser.add_argument('--separation', default=.9, type=float) # data generation
    parser.add_argument('--prop_missing', nargs='+', type=float, default=[.3])  # list of missing proportions
    parser.add_argument('--target_prop_missing', nargs='+', type=float, default=[.5])  # list of missing proportions
    parser.add_argument('--seed', default=0, type=int)
    parser.add_argument('--ct_kernel', default=0, type=int) # 0 for gibbs, 1 for MH
    parser.add_argument('--no_plots', action='store_true')
    return parser

if __name__ == "__main__":
    """
    "prediction speed":
    synthetic: CC + 1 column LR
    5 overlaid histograms of prediction time for one INFER of one target column.
    2 separate plots: 
    """
    import argparse
    import experiment_runner.experiment_utils as eru
    from experiment_runner.ExperimentRunner import ExperimentRunner, propagate_to_s3 

    parser = gen_parser()
    args = parser.parse_args()

    argsdict = eu.parser_args_to_dict(args)
    generate_plots = not argsdict['no_plots']

    results_filename = 'prediction_speed'
    dirname_prefix = 'prediction_speed'

    # this is where we actually run it.
    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')
    retval = er.do_experiments([argsdict], do_multiprocessing=False)

    if generate_plots:
        for i in er.frame.index:
            result = er._get_result(i)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_prediction_speed(result, filename=filename_img)
            pass
        pass

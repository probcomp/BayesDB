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

from bayesdb.client import Client
import experiment_utils as eu
import random
import numpy
import pylab
import time
import os

def run_experiment(argin):
    num_iters    = argin["num_iters"]
    num_chains   = argin["num_chains"]
    num_rows     = argin["num_rows"]
    num_cols     = argin["num_cols"]
    num_views    = argin["num_views"]
    num_clusters = argin["num_clusters"]
    prop_missing = argin["prop_missing"]
    separation   = argin["separation"]
    ct_kernel    = argin["ct_kernel"]

    multinomial_categories = argin["multinomial_categories"]
    seed = argin["seed"]

    random.seed(seed)

    # TODO: use dha.csv
    ofilename = "reasonably_calibrated_ofile.csv"
    table_name = 'reasonably_calibrated'

    argin['distargs'] = [{"K":multinomial_categories}]*num_cols
    argin['cctypes'] = ['multinomial']*num_cols
    argin['separation'] = [argin['separation']]*num_views

    T_array, structure = eu.gen_data(ofilename, argin, save_csv=True)

    filename, indices, col_names = eu.gen_missing_data_csv(ofilename, prop_missing, [])
    
    # create a client
    client = Client()

    # caluclate empirical frequency of each point
    frequencies = []
    for col in range(num_cols):
        frequencies.append(numpy.zeros(multinomial_categories))
    T_int = numpy.array(T_array, dtype=int)

    n_indices = len(indices[0])
    for i in range(n_indices):
        r = indices[0][i]
        c = indices[1][i]
        x = T_int[r,c]
        frequencies[c][x] += 1.0

    frequencies = [f/numpy.sum(f) for f in frequencies]
    
    # set up a dict fro the different config data
    result = dict()

    # do analyses
    for config in ['cc', 'crp', 'nb']:
        config_string = eu.config_map[config]
        table = table_name + '-' + config

        # drop old btable, create a new one with the new data and init models
        client('DROP BTABLE %s;' % table, yes=True)
        client('CREATE BTABLE %s FROM %s;' % (table, filename))
        client('INITIALIZE %i MODELS FOR %s %s;' % (num_chains, table, config_string))

        if ct_kernel == 1:
            client('ANALYZE %s FOR %i ITERATIONS WITH MH KERNEL;' % (table, num_iters) )
        else:
            client('ANALYZE %s FOR %i ITERATIONS;' % (table, num_iters) )


        # imput each index in indices and calculate the squared error
        results_config = []
        for col in range(num_cols):
            results_config.append(numpy.zeros(multinomial_categories))
        for col in range(num_cols):
            col_name = col_names[col]
            out = client("INFER %s FROM %s WITH CONFIDENCE .95 WITH 1 SAMPLES;" % (col_name, table), pretty=False, pandas_output=False)
            for i in range(n_indices):
                r = indices[0][i]
                c = indices[1][i]
                if c == col:
                    x = out[0]['data'][r][1]
                    results_config[c][int(x)] += 1.0

        results_config = [f/sum(f) for f in results_config]
        result[config] = results_config

    retval = dict()
    retval['actual_frequencies'] = frequencies
    retval['inferred_P_cc'] = result['cc']
    retval['inferred_P_crp'] = result['crp']
    retval['inferred_P_nb'] = result['nb']
    retval['config'] = argin

    return retval

def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_rows', default=200, type=int)                # number of rows in table
    parser.add_argument('--num_cols', default=4, type=int)                  # number of columns in table
    parser.add_argument('--num_views', default=2, type=int)                 # number of views
    parser.add_argument('--num_clusters', default=4, type=int)              # number of clusters per view
    parser.add_argument('--multinomial_categories', default=10, type=int)   
    parser.add_argument('--separation', default=.9, type=float)             # separation between clusters
    parser.add_argument('--num_iters', default=200, type=int)               # number of ANALYZE iterations
    parser.add_argument('--num_chains', default=2, type=int)                # number of MODELS
    parser.add_argument('--prop_missing', default=.2, type=float)           # proportion of data that is missing
    parser.add_argument('--seed', default=0, type=int)
    parser.add_argument('--ct_kernel', default=0, type=int)                 # 0 for Gibbs, 1 for MH
    parser.add_argument('--no_plots', action='store_true')

    return parser

if __name__ == "__main__":
    import argparse
    import experiment_runner.experiment_utils as eru
    from experiment_runner.ExperimentRunner import ExperimentRunner, propagate_to_s3 

    parser = gen_parser()
    args = parser.parse_args()

    argsdict = eu.parser_args_to_dict(args)
    generate_plots = not argsdict['no_plots']

    results_filename = 'reasonably_calibrated_errors_results'
    dirname_prefix = 'reasonably_calibrated_errors'

    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')
    er.do_experiments([argsdict])

    if generate_plots:
        for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_reasonably_calibrated_errors(result, filename=filename_img)
            pass
        pass    

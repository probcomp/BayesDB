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
    separation   = argin["separation"]
    seed         = argin["seed"]
    ct_kernel    = argin["ct_kernel"]

    if seed > 0:
        random.seed(seed)

    argin['cctypes'] = ['continuous']*num_cols
    argin['separation'] = [argin['separation']]*num_views

    # have to generate synthetic data
    filename = "exp_estimate_joint_ofile.csv"
    table_name = 'exp_estimate_joint'

    # generate starting data
    T_o, structure = eu.gen_data(filename, argin, save_csv=True)

    # generate a new csv with bottom row removed (held-out data)
    data_filename = 'exp_estimate_joint.csv'
    T_h = eu.gen_held_out_data(filename, data_filename, 1)

    # get the column names
    with open(filename, 'r') as f:
      csv_header = f.readline()
    col_names = csv_header.split(',')
    col_names[-1] = col_names[-1].strip()

    # set up a dict fro the different config data
    result = dict()

    true_held_out_p = []
    for col in range(num_cols):
        x = T_o[-1,col]
        logp = eu.get_true_logp(numpy.array([x]), col, structure)
        true_held_out_p.append(numpy.exp(logp))

    # start a client
    client = Client()

    # do analyses
    for config in ['cc', 'crp', 'nb']:
        config_string = eu.config_map[config]
        table = table_name + '-' + config

        # drop old btable, create a new one with the new data and init models
        client('DROP BTABLE %s;' % table, yes=True)
        client('CREATE BTABLE %s FROM %s;' % (table, data_filename))
        client('INITIALIZE %i MODELS FOR %s %s;' % (num_chains, table, config_string))

        these_ps = numpy.zeros(num_iters)
        these_ps_errors = numpy.zeros(num_iters)
        for i in range(num_iters):
            if ct_kernel == 1:
                client('ANALYZE %s FOR 1 ITERATIONS WITH MH KERNEL;' % table )
            else:
                client('ANALYZE %s FOR 1 ITERATIONS;' % table )

            # imput each index in indices and calculate the squared error
            mean_p = []
            mean_p_error = []
            for col in range(0,num_cols):
                col_name = col_names[col]
                x = T_o[-1,col]
                out = client('SELECT PROBABILITY OF %s=%f from %s;' % (col_name, x, table), pretty=False, pandas_output=False)
                p = out[0]['data'][0][1]

                mean_p.append(p)
                mean_p_error.append( (true_held_out_p[col]-p)**2.0 )

            these_ps[i] = numpy.mean(mean_p)
            these_ps_errors[i] = numpy.mean(mean_p_error)

        key_str_p = 'mean_held_out_p_' + config
        key_str_error = 'mean_error_' + config
        result[key_str_p] = these_ps
        result[key_str_error] = these_ps_errors

    retval = dict()
    retval['MSE_naive_bayes_indexer'] = result['mean_error_nb']
    retval['MSE_crp_mixture_indexer'] = result['mean_error_crp']
    retval['MSE_crosscat_indexer'] = result['mean_error_cc']

    retval['MEAN_P_naive_bayes_indexer'] = result['mean_held_out_p_nb']
    retval['MEAN_P_crp_mixture_indexer'] = result['mean_held_out_p_crp']
    retval['MEAN_P_crosscat_indexer'] = result['mean_held_out_p_cc']
    
    retval['config'] = argin

    return retval

def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_iters', default=100, type=int)
    parser.add_argument('--num_chains', default=20, type=int)
    parser.add_argument('--num_rows', default=300, type=int)
    parser.add_argument('--num_cols', default=20, type=int)
    parser.add_argument('--num_clusters', default=8, type=int)
    parser.add_argument('--num_views', default=4, type=int)
    parser.add_argument('--separation', default=.9, type=float)
    parser.add_argument('--seed', default=0, type=int)
    parser.add_argument('--ct_kernel', default=0, type=int)
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

    results_filename = 'estimate_the_full_joint_results'
    dirname_prefix = 'estimate_the_full_joint'

    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')
    er.do_experiments([argsdict])

    if generate_plots:
        for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_estimate_the_full_joint(result, filename=filename_img)
            pass
        pass

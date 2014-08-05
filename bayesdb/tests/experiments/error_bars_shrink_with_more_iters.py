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
from bayesdb.client import Client

import experiment_utils as eu
import csv
import random
import numpy
import pylab
import time
import math
import os
import scipy

def _get_prop_inferred(data, indices, col):
    count = 0.0
    total = 0.0

    # get the rows in this col that are missing
    rows = indices[0]
    cols = indices[1]
    idxs = range(len(indices[0]))
    missing_data_indices = [rows[i] for i in idxs if cols[i] == col]
    
    for row in missing_data_indices:
        if not math.isnan(data[row][1]):
            count += 1.0
        total += 1.0

    # if count < total:
    #     print "hit"
    return count/total

def run_experiment(argin):
    num_iters    = argin["num_iters"]
    num_chains   = argin["num_chains"]
    num_runs     = argin["num_runs"]
    prop_missing = argin["prop_missing"]
    confidence   = argin["confidence"]
    seed         = argin["seed"]

    n_queries = 2

    # random.seed(seed)

    # using dha, for now
    start_filename = "../data/dha.csv"
    table = 'exp_shrinks_with_iters'

    filename, indices, col_names = eu.gen_missing_data_csv(start_filename, prop_missing, [0])

    # get some random column pairs to do DEPENDENCE PROBABILITY queries on
    # don't do queries on the first column
    columns = range(1,len(col_names))
    column_queries = [ random.sample(columns, 2) for _ in range(n_queries)]

    dependence_queries = []
    for q in column_queries:
        col_1 = col_names[q[0]].lower()
        col_2 = col_names[q[1]].lower()
        this_query = "SELECT DEPENDENCE PROBABILITY OF %s WITH %s FROM %s;" % (col_1, col_2, table)
        dependence_queries.append(this_query)

    # get some inference queries
    column_queries = random.sample(columns, n_queries)
    infer_queries = []
    for q in column_queries:
        col = col_names[q].lower()
        this_query = 'INFER %s FROM %s WITH CONFIDENCE %f;' % (col, table, confidence)
        infer_queries.append(this_query)

    # create a client
    client = Client(testing=True)

    dependence_results = []
    inference_results = []
    for _ in range(num_runs):

        # drop old table, create new table, init models
        client('DROP BTABLE %s;' % table, yes=True)
        client('CREATE BTABLE %s FROM %s;' % (table, filename), pretty=False)
        client('INITIALIZE %i MODELS FOR %s;' % (num_chains, table), pretty=False)

        dependence_results_run = numpy.zeros((n_queries, num_iters))
        inference_results_run = numpy.zeros((n_queries, num_iters))

        for i in range(num_iters):
            # analyze
            client('ANALYZE %s FOR 1 ITERATIONS WAIT;' % (table) )

            # dependence
            for q in range(n_queries):
                out_dep = client(dependence_queries[q], pretty=False, pandas_output=False)
                dep = out_dep[0]['data'][0][1]
                dependence_results_run[q,i] = dep

            # infer
            for q in range(n_queries):
                out_inf = client(infer_queries[q], pretty=False, pandas_output=False)
                prop = _get_prop_inferred(out_inf[0]['data'], indices, column_queries[q])
                inference_results_run[q,i] = prop

        dependence_results.append( dependence_results_run )
        inference_results.append( inference_results_run )

    # calculate mean and errors (dependence)
    dep_means = numpy.zeros( (n_queries, num_iters) )
    dep_error = numpy.zeros( (n_queries, num_iters) )

    test_pass = True

    for i in range(num_iters):
        X = numpy.zeros( (n_queries,num_runs) )
        for r in range(num_runs):
            X[:,r] = dependence_results[r][:,i]        
        dep_means[:,i] = numpy.mean(X, axis=1)
        dep_error[:,i] = numpy.std(X, axis=1)/float(num_runs)**.5

        x = numpy.linspace(1,num_iters,num_iters)
        y = dep_error[:,i]
        slope, _, _, p_value, _ = scipy.stats.linregress(x,y)

        if not (slope < 0 and p_value < .05):
            test_pass = False


    # calculate mean and errors (infer)
    inf_means = numpy.zeros( (n_queries, num_iters) )
    inf_error = numpy.zeros( (n_queries, num_iters) )
    for i in range(num_iters):
        X = numpy.zeros( (n_queries,num_runs) )
        for r in range(num_runs):
            X[:,r] = inference_results[r][:,i]

        inf_means[:,i] = numpy.mean(X, axis=1)
        inf_error[:,i] = numpy.std(X, axis=1)/float(num_runs)**.5

        x = numpy.linspace(1,num_iters,num_iters)
        y = inf_error[:,i]
        slope, _, _, p_value, _ = scipy.stats.linregress(x,y)
        if not (slope < 0 and p_value < .05):
            test_pass = False

    result = dict()
    result['config'] = argin
    result['num_queries'] = n_queries
    result['iteration'] = range(1,num_iters+1)
    result['dependence_probability_mean'] = dep_means
    result['dependence_probability_error'] = dep_error
    result['infer_means'] = inf_means
    result['infer_stderr'] = inf_error
    result['pass'] = test_pass
    result['pass_criterion'] = "All errors have significant (p < .05), negative slope according to linear regression."

    print ( "%s: %s" % (result['pass_criterion'], result['pass']) )

    return result

def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_iters', default=100, type=int)
    parser.add_argument('--num_chains', default=20, type=int)
    parser.add_argument('--num_runs', default=5, type=int)
    parser.add_argument('--confidence', default=.1, type=float)
    parser.add_argument('--prop_missing', default=.2, type=float)
    parser.add_argument('--seed', default=0, type=int)
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

    results_filename = 'error_bars_shrink_results'
    dirname_prefix = 'error_bars_shrink'

    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')
    er.do_experiments([argsdict])
 
    if generate_plots:
        for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_error_bars_shrink(result, filename=filename_img)
            pass
        pass

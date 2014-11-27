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
import crosscat.tests.quality_tests.synthetic_data_generator as sdg

import experiment_utils as eu
import itertools
import csv
import random
import numpy
import pylab
import time
import math
import os

from scipy.misc import comb


def generate_data(num_rows, num_ones_cols):
    """
    Generate num_rows by 2**num_rows matrix of ones and zeros where the first num_ones_cols columns
    are all 1.
    """
    T_array = numpy.round(numpy.random.rand(num_rows, 2**num_rows));
    T_array[:,0:num_ones_cols] = 1
    return T_array


def generate_dependence_queries(num_ones_cols, col_names, table_name, num_indep_queries):
    columns_list = range(num_ones_cols,len(col_names))
    column_pairs = itertools.combinations(columns_list, 2)
    num_cols = len(columns_list)

    num_pairs = int(comb(num_cols, 2))
    pairs_range = range(num_pairs)
    if num_indep_queries >= num_pairs:
        take_pairs = range(num_pairs)
    else:
        take_pairs = random.sample(pairs_range, num_indep_queries)

    queries = []
    target_marker = []
    for a, b in itertools.permutations(range(num_ones_cols), 2):
        col_a = col_names[a]
        col_b = col_names[b]
        q = "SELECT DEPENDENCE PROBABILITY OF %s WITH %s FROM %s;" % (col_a, col_b, table_name)
        queries.append(q)
        target_marker.append(True)

    pairs = []
    pair_idx = 0
    for pair in column_pairs:
        if pair_idx in take_pairs:
            c1 = pair[0]
            c2 = pair[1]
            n1 = col_names[c1]
            n2 = col_names[c2]
            q = "SELECT DEPENDENCE PROBABILITY OF %s WITH %s FROM %s;" % (n1, n2, table_name)
            queries.append(q)
            pairs.append( [c1,c2] ) 
            target_marker.append(False)
        pair_idx += 1

    assert len(target_marker) == len(queries)

    # pdb.set_trace()
    return queries, pairs, target_marker


def run_experiment(argin):
    num_iters = argin["num_iters"]
    num_chains = argin["num_chains"]
    num_rows = argin["num_rows"]
    num_indep_queries = argin["num_indep_queries"]
    ct_kernel = argin["ct_kernel"]
    num_ones_cols = argin["num_ones_cols"]
    collect_lag = argin["collect_lag"]

    seed = argin["seed"]

    col_names = [ "col_%i" % i for i in range(2**num_rows)]

    T_array = generate_data(num_rows, num_ones_cols)
    T = T_array.tolist()

    # save file to .csv
    exp_path = 'expdata/cf/'
    eu.make_folder(exp_path)
    filename = exp_path + "coin_flip_exp.csv"
    table = "coin_flip_exp"
    T.insert(0, col_names)
    eu.list_to_csv(filename, T)

    result = dict()

    queries, pairs, target_marker = generate_dependence_queries(num_ones_cols, 
                                                                col_names, table, 
                                                                num_indep_queries)

    num_queries = len(queries)
    dependence_probs = numpy.zeros( (num_iters/collect_lag+1, num_queries) )

    client = Client()

    client('DROP BTABLE %s;' % table, yes=True)
    client('CREATE BTABLE %s FROM %s;' % (table, filename), yes=True, key_column=0, pretty=False)

    for col in col_names:
        client('UPDATE SCHEMA FOR %s SET %s=categorical(2)' % (table, col), pretty=False)

    # client("SHOW SCHEMA FOR %s" % table)

    init_string = 'INITIALIZE %i MODELS FOR %s;' % (num_chains, table)
    client(init_string, pretty=False)

    # do the analyses
    for q in range(num_queries):
        query = queries[q]
        out = client(query, pretty=False, pandas_output=False)
        dependence_probs[0,q] = out[0]['data'][0][1]

    total_iters = 0;
    i = 1
    x = [0]
    while total_iters < num_iters:

        if ct_kernel == 1:
            client( 'ANALYZE %s FOR %i ITERATIONS WITH MH KERNEL WAIT;' % (table, collect_lag) )
        else:
            client( 'ANALYZE %s FOR %i ITERATIONS WAIT;' % (table, collect_lag) )

        for q in range(num_queries):
            query = queries[q]
            out = client(query, pretty=False, pandas_output=False)
            dependence_probs[i,q] = out[0]['data'][0][1]

        total_iters += collect_lag
        i += 1
        x.append(total_iters)

    result['dependence_probs'] = dependence_probs
    result['iteration_index'] = x
    result['target_marker'] = target_marker
    result['config'] = argin
    result['data'] = T_array

    return result


def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_rows', default=10, type=int)             # number of rows
    parser.add_argument('--num_ones_cols', default=2, type=int)         # number of all-ones columns to insert
    parser.add_argument('--num_indep_queries', default=20, type=int)    # number of dependece probability queries
    parser.add_argument('--num_chains', default=8, type=int)            # number of chains (samples)
    parser.add_argument('--num_iters', default=500, type=int)           # number of ANALYZE iterations
    parser.add_argument('--seed', default=0, type=int)                  # data seed
    parser.add_argument('--ct_kernel', default=0, type=int)             # which kernel 0 for gibbs, 1 for MH
    parser.add_argument('--collect_lag', default=10, type=int)          # number of iteratrions to run each colelction
    parser.add_argument('--no_plots', action='store_true')              # do not plot
    parser.add_argument('--no_runner', action='store_true')             # do not use experiment runner

    return parser


if __name__ == "__main__":
    # python coin_flip.py --num_rows 10 --num_iters 100 --num_ones_cols 3
    import argparse
    import experiment_runner.experiment_utils as eru
    from experiment_runner.ExperimentRunner import ExperimentRunner, propagate_to_s3 

    parser = gen_parser()
    args = parser.parse_args()

    argsdict = eu.parser_args_to_dict(args)
    generate_plots = not argsdict['no_plots']

    use_runner = not argsdict['no_runner']

    results_filename = 'coin_flip_results'
    dirname_prefix = 'coin_flip'

    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')

    if use_runner:
        er.do_experiments([argsdict], do_multiprocessing=False)

        if generate_plots:
            for id in er.frame.index:
                result = er._get_result(id)
                this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
                filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
                eu.plot_coin_flip(result, filename=filename_img)
                pass
    else:
        result = run_experiment(argsdict)

        if generate_plots:
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.make_folder(os.path.join(dirname_prefix, this_dirname))
            eu.plot_coin_flip(result, filename=filename_img)
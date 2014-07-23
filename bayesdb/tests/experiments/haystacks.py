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

def generate_dependence_queries(needle_a_cols, needle_b_cols, col_names, table_name, num_indep_queries):
    columns_list = range(4,len(col_names))
    column_pairs = itertools.combinations(columns_list, 2)
    num_cols = len(columns_list)


    num_pairs = int(comb(num_cols-4, 2))
    pairs_range = range(num_pairs)
    if num_indep_queries >= num_pairs:
        take_pairs = range(num_pairs)
    else:
        take_pairs = random.sample(pairs_range, num_indep_queries)

    pairs = [(0,1),(2,3)]

    q1 = "SELECT DEPENDENCE PROBABILITY OF %s WITH %s FROM %s;" % (needle_a_cols[0], needle_a_cols[1], table_name)
    q2 = "SELECT DEPENDENCE PROBABILITY OF %s WITH %s FROM %s;" % (needle_b_cols[0], needle_b_cols[1], table_name)

    queries = [q1,q2]

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
        pair_idx += 1

    return queries, pairs

def run_experiment(argin):
    num_iters = argin["num_iters"]
    num_chains = argin["num_chains"]
    num_rows = argin["num_rows"]
    num_cols = argin["num_cols"]
    with_id = argin["with_id"]
    needles = argin["needles"]
    mixed_types = argin["mixed_types"]
    multinomial_categories = argin["multinomial_categories"]
    separation = argin["separation"]
    num_indep_queries = argin["num_indep_queries"]
    independent_clusters = argin["independent_clusters"]
    ct_kernel = argin["ct_kernel"]

    seed = argin["seed"]

    if seed > 0:
        random.seed(seed)

    # generate column indices and header
    col_names = [ "col_%i" % i for i in range(num_cols)]

    if mixed_types and multinomial_categories > 0:
        data_mode = 'mixed'
    elif multinomial_categories > 0:
        data_mode = 'multinomial'
    else:
        data_mode = 'continuous'

    if needles:
        T = [[0]*num_cols]*num_rows
        Zv = [0,0,1,1] # our needles
        Zv.extend(range(2,num_cols-2))
        # random.shuffle(Zv)

        num_views = max(Zv)+1

        separation = [.95]*2
        separation.extend([0.0]*(num_views-2))

        min_clusters = 4
        max_clusters = 5

        cluster_weights = []
        # generate weights. 
        for v in range(num_views):
            if v < 2:
                num_clusters = random.randrange(min_clusters, max_clusters)
            else:
                if independent_clusters:
                    num_clusters = random.randrange(min_clusters, max_clusters)
                else:
                    num_clusters = 1

            cluster_weights.append( [1.0/num_clusters]*num_clusters ) 

        cctypes, distargs = eu.get_column_types(data_mode, num_cols, multinomial_categories)
        T, _ = sdg.gen_data(cctypes, num_rows, Zv, cluster_weights, separation, distargs=distargs)
    else:
        T, cctypes = eu.generate_noise(data_mode, num_rows, num_cols)


    # # preprend the row_id
    # if with_id:
    #     needle_a_cols = (1,2)
    #     needle_b_cols = (3,4)
    #     col_names.insert(0, 'ID')
    #     # TODO: ID type
    #     cctypes.insert(0,'continuous')
    #     # header = "ID,%s" % header
    #     if needles:
    #         Zv.insert(0, num_views)
    #     for row in range(num_rows):
    #         T[row].insert(0, row)
    # else:
    needle_a_cols = (col_names[0],col_names[1])
    needle_b_cols = (col_names[2],col_names[3])

    # save file to .csv
    filename = "needles_exp.csv"
    table = "needles_exp"
    T.insert(0, col_names)
    eu.list_to_csv(filename, T)

    # generate queries
    queries, pairs = generate_dependence_queries(needle_a_cols, needle_b_cols,
                        col_names, table, num_indep_queries)
    num_queries = len(queries)

    dependence_probs = numpy.zeros( (num_iters, num_queries) )

    client = Client()

    client('DROP BTABLE %s;' % table, yes=True)
    client('CREATE BTABLE %s FROM %s;' % (table, filename))
    init_string = 'INITIALIZE %i MODELS FOR %s;' % (num_chains, table)
    print init_string 
    client(init_string)
    client('SHOW DIAGNOSTICS FOR %s;' % table)

    # do the analyses
    for i in range(num_iters):
        if ct_kernel == 1:
            client( 'ANALYZE %s FOR 1 ITERATIONS WITH MH KERNEL WAIT;' % table )
        else:
            client( 'ANALYZE %s FOR 1 ITERATIONS WAIT;' % table )

        for q in range(num_queries):
            query = queries[q]
            out = client(query, pretty=False, pandas_output=False)
            dependence_probs[i,q] = out[0]['data'][0][1]

    result = dict()
    # store the queries in result
    result['query_col1'] = []
    result['query_col2'] = []
    result['dependence_probs'] = dependence_probs
    for pair in pairs:
        result['query_col1'].append(pair[0])
        result['query_col2'].append(pair[1])
    
    # for each query, get wether those columns were actually independent
    independent = [True]*num_queries
    if needles:
        for i in range(num_queries):
            col_idx_0 = pairs[i][0]
            col_idx_1 = pairs[i][1]            
            if Zv[col_idx_0] == Zv[col_idx_1]:
                independent[i] = False

    result['cols_independent'] = independent
    result['config'] = argin
    result['config']['data_mode'] = data_mode

    client('SHOW DIAGNOSTICS FOR %s;' % table)

    return result

def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_rows', default=100, type=int)
    parser.add_argument('--num_cols', default=20, type=int)
    parser.add_argument('--multinomial_categories', default=0, type=int)
    parser.add_argument('--num_iters', default=100, type=int)
    parser.add_argument('--num_chains', default=8, type=int)
    parser.add_argument('--separation', default=.9, type=float) # separation (0-1) between clusters
    parser.add_argument('--needles', action='store_true')
    parser.add_argument('--mixed_types', action='store_true')   # use multinomial and continuous
    parser.add_argument('--with_id', action='store_true')       # simulate an ID column (unique integer values)
    parser.add_argument('--seed', default=0, type=int)
    parser.add_argument('--ct_kernel', default=0, type=int)     # 0 for Gibbs, 1 for MH
    parser.add_argument('--no_plots', action='store_true')
    parser.add_argument('--independent_clusters', action='store_true')  # clusters or correlated data
    parser.add_argument('--num_indep_queries', default=10, type=int)    # num column dependence queries for noise columns 

    return parser

if __name__ == "__main__":
    
    import argparse
    import experiment_runner.experiment_utils as eru
    from experiment_runner.ExperimentRunner import ExperimentRunner, propagate_to_s3 

    parser = gen_parser()
    args = parser.parse_args()

    argsdict = eu.parser_args_to_dict(args)
    generate_plots = not argsdict['no_plots']

    results_filename = 'haystacks_results'
    dirname_prefix = 'haystacks'

    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')
    er.do_experiments([argsdict])

    if generate_plots:
        for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_haystacks(result, filename=filename_img)
            pass
        pass

    
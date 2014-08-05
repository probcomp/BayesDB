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

def take_T_column_subset(T, which_cols ):
    T_sub = []
    for row in range(len(T)):
        row_data = []
        for col in which_cols:
            row_data.append( T[row][col])
        T_sub.append(row_data)
    return T_sub

def generate_dependence_queries(needle_a_cols, needle_b_cols, col_names, table_name, num_indep_queries):
    columns_list = range(4,len(col_names))
    column_pairs = itertools.combinations(columns_list, 2)
    num_cols = len(columns_list)

    num_pairs = int(comb(num_cols, 2))
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
    max_cols = argin["max_cols"]
    rho = argin["rho"]
    num_indep_queries = argin["num_indep_queries"]
    independent_clusters = argin["independent_clusters"]
    ct_kernel = argin["ct_kernel"]
    multimodal = argin["multimodal"]
    separation = argin["separation"]

    all_cols = max_cols + 4 # max_cols plus number of dependent columns

    seed = argin["seed"]

    if seed > 0:
        random.seed(seed)
        numpy.random.seed(seed)

    # build full data file
    # generate column indices and header
    col_names = [ "col_%i" % i for i in range(all_cols)]

    Zv = [0,0,1,1] # our needles
    Zv.extend(range(2,all_cols-2))

    min_clusters = 3
    max_clusters = 10

    T_array = numpy.zeros( (num_rows, all_cols) )

    Sigma = numpy.array( [[1.0,rho],[rho,1.0]])
    mu = numpy.array([0,0])

    if multimodal:
        T = [[0]*num_cols]*num_rows
        Zv = [0,0,1,1] # our needles
        Zv.extend(range(2,num_cols-2))
        random.shuffle(Zv)

        num_views = max(Zv)+1

        separation = [separation]*2
        separation.extend([separation]*(num_views-2))

        min_clusters = 4
        max_clusters = 5

        cluster_weights = []
        # generate weights. 
        for v in range(num_views):
            if v < 2:
                num_clusters = random.randrange(min_clusters, max_clusters)
            else:
                num_clusters = 1
            cluster_weights.append( [1.0/num_clusters]*num_clusters ) 

        cctypes, distargs = eu.get_column_types(data_mode, num_cols, multinomial_categories)
        T, _ = sdg.gen_data(cctypes, num_rows, Zv, cluster_weights, separation, distargs=distargs)
        T_array = numpy.array(T)
    else:
        T_array[:, 0:1+1] = numpy.random.multivariate_normal(mu, Sigma, num_rows)
        T_array[:, 2:3+1] = numpy.random.multivariate_normal(mu, Sigma, num_rows)
        separation = .5
        for col in range(4, all_cols):
            num_clusters = random.randrange(min_clusters, max_clusters)+1
            for row in range(num_rows):
                k = random.randrange(num_clusters)
                T_array[row, col] = numpy.random.randn()+k*6*separation

        T = T_array.tolist()

    # save file to .csv
    exp_path = 'expdata/hb/'
    eu.make_folder(exp_path)
    filename = exp_path + "haystack_break_exp.csv"
    table = "haystack_break_exp"
    T.insert(0, col_names)
    eu.list_to_csv(filename, T)
    # done building data file

    # get colum step size (powers of two)
    num_steps = int( math.log(max_cols, 2) )-1
    step_size = [2**t for t in range(2, num_steps+1)]

    assert step_size[-1] <= max_cols

    if step_size[-1] < max_cols:
        step_size.append(max_cols)

    assert step_size[0] == 4 and step_size[-1] == max_cols

    # the needle column names
    needle_a_cols = (col_names[0],col_names[1])
    needle_b_cols = (col_names[2],col_names[3])

    result = dict()
    result['steps'] = []

    for num_distractor_columns in step_size:
        # create subdata
        T_sub = take_T_column_subset(T, range(4+num_distractor_columns) )
        subpath = exp_path+'d_'+str(num_distractor_columns)+'/'
        eu.make_folder(subpath)
        subfilename = subpath + "haystack_break_exp_" + str(num_distractor_columns) + ".csv"
        eu.list_to_csv(subfilename, T_sub)

        col_names_sub = T_sub[0]

        # generate queries
        queries, pairs = generate_dependence_queries(needle_a_cols, needle_b_cols,
                            col_names_sub, table, num_indep_queries)
        num_queries = len(queries)

        dependence_probs = numpy.zeros( (num_iters+1, num_queries) )

        client = Client(testing=True)

        client('DROP BTABLE %s;' % table, yes=True)
        client('CREATE BTABLE %s FROM %s;' % (table, subfilename))
        init_string = 'INITIALIZE %i MODELS FOR %s;' % (num_chains, table)
        print init_string 
        client(init_string)

        # do the analyses
        for i in range(0,num_iters+1):
            if i > 0:
                if ct_kernel == 1:
                    client( 'ANALYZE %s FOR 1 ITERATIONS WITH MH KERNEL WAIT;' % table )
                else:
                    client( 'ANALYZE %s FOR 1 ITERATIONS WAIT;' % table )

            for q in range(num_queries):
                query = queries[q]
                out = client(query, pretty=False, pandas_output=False)
                dependence_probs[i,q] = out[0]['data'][0][1]

        subresult = dict()
        # store the queries in subresult
        subresult['query_col1'] = []
        subresult['query_col2'] = []
        subresult['dependence_probs'] = dependence_probs
        for pair in pairs:
            subresult['query_col1'].append(pair[0])
            subresult['query_col2'].append(pair[1])
        
        # for each query, get wether those columns were actually independent
        independent = [True]*num_queries
        for i in range(num_queries):
            col_idx_0 = pairs[i][0]
            col_idx_1 = pairs[i][1]            
            if Zv[col_idx_0] == Zv[col_idx_1]:
                independent[i] = False

        subresult['cols_independent'] = independent
        subresult['distractor_cols'] = num_distractor_columns
        result['steps'].append(subresult)
    
    result['config'] = argin
    result['data'] = T_array

    pass_criterion = "On last iteration, dependent columns have >= .5 dependence probability and independent columns have <= .2 dependence probability"
    pass = True
    for step_result in result['steps']:
        independent = step_result['cols_independent']
        dependence_probs = step_result['dependence_probs']
        for q in range(len(independent)):
            is_needle = not independent[q]
            if is_needle:
                if dependence_probs[-1:q] < .5:
                    pass = False
                    break
            else:
                if dependence_probs[-1:q] > .2:
                    break
                    pass = False
        if not pass:
            break
                
    result['pass'] = pass
    result['pass_criterion'] = pass_criterion

    print("%s: %s" % (pass_criterion, pass))
    
    return result


def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_rows', default=100, type=int)            # number of rows
    parser.add_argument('--max_cols', default=500, type=int)            # number of distractor cols
    parser.add_argument('--num_indep_queries', default=20, type=int)    # number of dependece probability queries
    parser.add_argument('--multimodal', action='store_true')            # use multimodal (opposed to correlated) depedendent cols
    parser.add_argument('--separation', default=.9, type=int)           # separation of multimodal dependent cols
    parser.add_argument('--rho', default=.95, type=float)               # correlation of unimodal columns
    parser.add_argument('--independent_clusters', action='store_true')  # disractor columns have multimodal data

    parser.add_argument('--num_iters', default=100, type=int)           # number of transitions (iterations)
    parser.add_argument('--num_chains', default=8, type=int)            # number of chains (samples)
    parser.add_argument('--seed', default=0, type=int)                  # data seed
    parser.add_argument('--ct_kernel', default=0, type=int)             # which kernel 0 for gibbs, 1 for MH
    parser.add_argument('--no_plots', action='store_true')              # do not plot
    parser.add_argument('--no_runner', action='store_true')             # do not use experiment runner
    
    return parser



if __name__ == "__main__":
    # python haystacks_break.py --num_rows 30 --max_cols 64 --num_chains 8 --rho .9 --save_pickle
    import argparse
    import experiment_runner.experiment_utils as eru
    from experiment_runner.ExperimentRunner import ExperimentRunner, propagate_to_s3 

    parser = gen_parser()
    args = parser.parse_args()

    argsdict = eu.parser_args_to_dict(args)
    generate_plots = not argsdict['no_plots']

    use_runner = not argsdict['no_runner']

    results_filename = 'haystacks_break_results'
    dirname_prefix = 'haystacks_break'

    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')

    if use_runner:
        er.do_experiments([argsdict], do_multiprocessing=False)

        if generate_plots:
            for id in er.frame.index:
                result = er._get_result(id)
                this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
                filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
                eu.plot_haystacks_break(result, filename=filename_img)
                pass
    else:
        result = run_experiment(argsdict)

    	if generate_plots:
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
   	    eu.make_folder(os.path.join(dirname_prefix, this_dirname))
            eu.plot_haystacks_break(result, filename=filename_img)


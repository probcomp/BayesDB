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
import crosscat.cython_code.State as State
import crosscat.utils.sample_utils as su
import crosscat.utils.data_utils as du

import experiment_utils as eu
import time
import numpy
import pylab
import sys
import os

table_string = dict(
    sinwave="exp_sinwave",
    x="exp_x",
    ring="exp_ring",
    dots="exp_dots")

# Save data files to .csv
def gen_shapetest_csvs(num_rows):
    sinwave_data = eu.gen_sine_wave(num_rows)
    numpy.savetxt("exp_sinwave.csv", sinwave_data, delimiter=",", header="x,y", comments='')
    x_data = eu.gen_x(num_rows)
    numpy.savetxt("exp_x.csv", x_data, delimiter=",", header="x,y", comments='')
    ring_data = eu.gen_ring(num_rows)
    numpy.savetxt("exp_ring.csv", ring_data, delimiter=",", header="x,y", comments='')
    dots_data = eu.gen_four_dots(num_rows)
    numpy.savetxt("exp_dots.csv", dots_data, delimiter=",", header="x,y", comments='')

    ret = dict(sinwave=sinwave_data, x=x_data, ring=ring_data, dots=dots_data)

    return ret

def gen_base_queries(num_iters, num_chains, num_rows, shape, ct_kernel):
    table = table_string[shape]
    datafile = table + '.csv'

    cmd_list = []
    # load the data into a table
    cmd_list.append("CREATE BTABLE %s FROM %s;" % (table, datafile) )
    # intialize models
    cmd_list.append('INITIALIZE %i MODELS FOR %s;' % (num_chains, table) )
    # analyze the data
    if ct_kernel == 1:
        cmd_list.append('ANALYZE %s FOR %i ITERATIONS WITH MH KERNEL;' % (table, num_iters) )
    else:
        cmd_list.append('ANALYZE %s FOR %i ITERATIONS;' % (table, num_iters) )
    # simulate new data
    

    return cmd_list

def gen_data_crosscat(mode, T):
    # edit transition list according to 
    
    all_transitions = []

    M_c = du.gen_M_c_from_T(T, cctypes=['continuous']*2)

    state = State.p_state(M_c, T)
    if mode == 'crp_mixture':
        # fix the views
        X_D = state.get_X_D();
        X_L = state.get_X_L();
        X_D = [X_D[0]]
        X_L['column_partition']['assignments'] = [1,1]
        state = State.p_state(M_c, T, X_L=X_L, X_D=X_D)


def run_experiment(argin):
    num_rows = argin["num_rows"]
    num_iters = argin["num_iters"]
    num_chains = argin["num_chains"]
    ct_kernel = argin["ct_kernel"]

    # generate the data
    datasets = gen_shapetest_csvs(num_rows)

    client = Client()

    # drop tables
    print "Dropping tables."
    client('DROP BTABLE exp_sinwave;', yes=True)
    client('DROP BTABLE exp_x;', yes=True)
    client('DROP BTABLE exp_ring;', yes=True)
    client('DROP BTABLE exp_dots;', yes=True)

    plt = 0

    data_out = dict()
    data_out['config'] = argin;

    # recreate sin wave
    for shape in ["sinwave", "x", "ring", "dots"]:
        query_list = gen_base_queries(num_iters, num_chains, num_rows, shape, ct_kernel);
        for query in query_list:
            print query
            client(query)

        table = table_string[shape]
        datafile = table + '.csv'

        out = client('SIMULATE x,y FROM %s TIMES %i;' % (table, num_rows), pretty=False)

        X_original = datasets[shape]
        X_inferred = numpy.array(out[0])

        # get the logps
        # latent_states = client.engine.persistence_layer.get_latent_states(table)
        # X_L_list = latent_states[0]
        # logps = [X_L['logp'] for X_L in X_L_list]
        

        # this_key = shape + "_logps"
        # data_out[this_key] = logps

        this_key = shape + "_inferred"
        data_out[this_key] = X_inferred

        this_key = shape + "_original"
        data_out[this_key] = X_original

    return data_out

def gen_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_rows', default=500, type=int)
    parser.add_argument('--num_iters', default=200, type=int)
    parser.add_argument('--num_chains', default=1, type=int)
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

    results_filename = 'recovers_original_densities_results'
    dirname_prefix = 'recovers_original_densities'

    er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, bucket_str='experiment_runner', storage_type='fs')
    er.do_experiments([argsdict])

    if generate_plots:
        for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_recovers_original_densities(result, filename=filename_img)
            pass
        pass

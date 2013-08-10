#!/opt/anaconda/bin/python

#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import os
import numpy
import sys
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.hadoop_utils as hu
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.python_utils.general_utils as gu
import tabular_predDB.python_utils.timing_test_utils as ttu
import tabular_predDB.python_utils.convergence_test_utils as ctu
import tabular_predDB.LocalEngine as LE
import tabular_predDB.HadoopEngine as HE
from tabular_predDB.settings import Hadoop as hs


def initialize_helper(table_data, data_dict, command_dict):
    M_c = table_data['M_c']
    M_r = table_data['M_r']
    T = table_data['T']
    SEED = data_dict['SEED']
    initialization = command_dict['initialization']
    engine = LE.LocalEngine(SEED)
    X_L, X_D = engine.initialize(M_c, M_r, T, initialization=initialization)
    SEED = engine.get_next_seed()
    #
    ret_dict = dict(SEED=SEED, X_L=X_L, X_D=X_D)
    return ret_dict

def analyze_helper(table_data, data_dict, command_dict):
    M_c = table_data['M_c']
    T = table_data['T']
    SEED = data_dict['SEED']
    X_L = data_dict['X_L']
    X_D = data_dict['X_D']
    kernel_list = command_dict['kernel_list']
    n_steps = command_dict['n_steps']
    c = command_dict['c']
    r = command_dict['r']
    max_time = command_dict['max_time']
    engine = LE.LocalEngine(SEED)
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=kernel_list,
                                          n_steps=n_steps, c=c, r=r,
                                          max_time=max_time)
    SEED = engine.get_next_seed()
    #
    ret_dict = dict(SEED=SEED, X_L=X_L_prime, X_D=X_D_prime)
    return ret_dict

def chunk_analyze_helper(table_data, data_dict, command_dict):
    original_n_steps = command_dict['n_steps']
    original_SEED = data_dict['SEED']
    chunk_size = command_dict['chunk_size']
    chunk_filename_prefix = command_dict['chunk_filename_prefix']
    chunk_dest_dir = command_dict['chunk_dest_dir']
    #
    steps_done = 0
    while steps_done < original_n_steps:
        steps_remaining = original_n_steps - steps_done
        command_dict['n_steps'] = min(chunk_size, steps_remaining)
        ith_chunk = steps_done / chunk_size
        dict_out = analyze_helper(table_data, data_dict, command_dict)
        data_dict.update(dict_out)
        # write to hdfs
        chunk_filename = '%s_seed_%s_chunk_%s.pkl.gz' \
            % (chunk_filename_prefix, original_SEED, ith_chunk)
        fu.pickle(dict_out, chunk_filename)
        hu.put_hdfs(None, chunk_filename, chunk_dest_dir)
        #
        steps_done += chunk_size
    chunk_filename = '%s_seed_%s_chunk_%s.pkl.gz' \
        % (chunk_filename_prefix, original_SEED, 'FINAL')
    fu.pickle(dict_out, chunk_filename)
    hu.put_hdfs(None, chunk_filename, chunk_dest_dir)
    return dict_out
    
def time_analyze_helper(table_data, data_dict, command_dict):
    # FIXME: this is a kludge
    command_dict.update(data_dict)
    #
    gen_seed = data_dict['SEED']
    num_clusters = data_dict['num_clusters']
    num_cols = data_dict['num_cols']
    num_rows = data_dict['num_rows']
    num_views = data_dict['num_views']

    T, M_c, M_r, X_L, X_D = ttu.generate_clean_state(gen_seed,
                                                 num_clusters,
                                                 num_cols, num_rows,
                                                 num_views,
                                                 max_mean=10, max_std=1)
    table_data = dict(T=T,M_c=M_c)

    data_dict['X_L'] = X_L
    data_dict['X_D'] = X_D
    start_dims = du.get_state_shape(X_L)
    with gu.Timer('time_analyze_helper', verbose=False) as timer:
        inner_ret_dict = analyze_helper(table_data, data_dict, command_dict)
    end_dims = du.get_state_shape(inner_ret_dict['X_L'])
    T = table_data['T']
    table_shape = (len(T), len(T[0]))
    ret_dict = dict(
        table_shape=table_shape,
        start_dims=start_dims,
        end_dims=end_dims,
        elapsed_secs=timer.elapsed_secs,
        kernel_list=command_dict['kernel_list'],
        n_steps=command_dict['n_steps'],
        )
    return ret_dict

def convergence_analyze_helper(table_data, data_dict, command_dict):
    gen_seed = data_dict['SEED']
    num_clusters = data_dict['num_clusters']
    num_cols = data_dict['num_cols']
    num_rows = data_dict['num_rows']
    num_views = data_dict['num_views']
    max_mean = data_dict['max_mean']
    num_transitions = data_dict['n_steps']
    block_size = data_dict['block_size']
    init_seed = data_dict['init_seed']
    
    T, M_r, M_c, data_inverse_permutation_indices = du.gen_factorial_data_objects(gen_seed, num_clusters,
                                                                                  num_cols, num_rows, num_views,
                                                                                  max_mean=max_mean, max_std=1,
                                                                                  send_data_inverse_permutation_indices=True)
    view_assignment_truth, X_D_truth = ctu.truth_from_permute_indices(data_inverse_permutation_indices, \
                                                                      num_rows,num_cols, num_views, num_clusters)

    ari_table = []
    ari_views = []
    
    engine=LE.LocalEngine(init_seed)
    M_c_prime, M_r_prime, X_L, X_D = \
               engine.initialize(M_c, M_r, T, initialization='from_the_prior')
    
    view_assignments = X_L['column_partition']['assignments']
    #tmp_ari_table, tmp_ari_views = ctu.multi_chain_ARI(X_L_list,X_D_list, view_assignment_truth, X_D_truth)
    tmp_ari_table, tmp_ari_views = ctu.ARI_CrossCat(numpy.asarray(view_assignments), numpy.asarray(X_D), numpy.asarray(view_assignment_truth), numpy.asarray(X_D_truth))
    ari_table.append(tmp_ari_table)
    ari_views.append(tmp_ari_views)
    

    completed_transitions = 0
    n_steps = min(block_size, num_transitions)
    
    while (completed_transitions < num_transitions):
        # We won't be limiting by time in the convergence runs
        X_L, X_D = engine.analyze(M_c, T, X_L, X_D, kernel_list=(), \
                                            n_steps=n_steps, max_time=-1)
        completed_transitions = completed_transitions+block_size
        
        view_assignments = X_L['column_partition']['assignments']
        tmp_ari_table, tmp_ari_views = ctu.ARI_CrossCat(numpy.asarray(view_assignments), numpy.asarray(X_D), numpy.asarray(view_assignment_truth), numpy.asarray(X_D_truth))
        ari_table.append(tmp_ari_table)
        ari_views.append(tmp_ari_views)
        
    ret_dict = dict(
        num_rows=num_rows,
        num_cols=num_cols,
        num_views=num_views,
        num_clusters=num_clusters,
        max_mean = max_mean,
        ari_table=ari_table,
        ari_views=ari_views,
        n_steps=num_transitions,
        block_size=block_size,
        )
    return ret_dict
    

method_lookup = dict(
    initialize=initialize_helper,
    analyze=analyze_helper,
    time_analyze=time_analyze_helper,
    convergence_analyze=convergence_analyze_helper,
    chunk_analyze=chunk_analyze_helper,
    )


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--table_data_filename', type=str,
                        default=hs.default_table_data_filename)
    parser.add_argument('--command_dict_filename', type=str,
                        default=hs.default_command_dict_filename)
    args = parser.parse_args()
    table_data_filename = args.table_data_filename
    command_dict_filename = args.command_dict_filename
    
    
    table_data = fu.unpickle(table_data_filename)
    command_dict = fu.unpickle(command_dict_filename)
    command = command_dict['command']
    method = method_lookup[command]
    #
    from signal import signal, SIGPIPE, SIG_DFL 
    signal(SIGPIPE,SIG_DFL) 
    for line in sys.stdin:
        key, data_dict = xu.parse_hadoop_line(line)
        ret_dict = method(table_data, data_dict, command_dict)
        xu.write_hadoop_line(sys.stdout, key, ret_dict)

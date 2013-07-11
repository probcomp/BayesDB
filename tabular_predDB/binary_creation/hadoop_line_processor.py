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
import sys
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.python_utils.general_utils as gu
import tabular_predDB.LocalEngine as LE
import tabular_predDB.HadoopEngine as HE


def initialize_helper(table_data, dict_in):
    M_c = table_data['M_c']
    M_r = table_data['M_r']
    T = table_data['T']
    initialization = dict_in['initialization']
    SEED = dict_in['SEED']
    engine = LE.LocalEngine(SEED)
    M_c_prime, M_r_prime, X_L, X_D = \
               engine.initialize(M_c, M_r, T, initialization=initialization)
    #
    ret_dict = dict(X_L=X_L, X_D=X_D)
    return ret_dict

def analyze_helper(table_data, dict_in):
    M_c = table_data['M_c']
    T = table_data['T']
    X_L = dict_in['X_L']
    X_D = dict_in['X_D']
    kernel_list = dict_in['kernel_list']
    n_steps = dict_in['n_steps']
    c = dict_in['c']
    r = dict_in['r']
    max_time = dict_in['max_time']
    SEED = dict_in['SEED']
    engine = LE.LocalEngine(SEED)
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=kernel_list,
                                          n_steps=n_steps, c=c, r=r,
                                          max_time=max_time)
    #
    ret_dict = dict(X_L=X_L_prime, X_D=X_D_prime)
    return ret_dict

def chunk_analyze_helper(table_data, dict_in):
    original_n_steps = dict_in['n_steps']
    original_SEED = dict_in['SEED']
    chunk_size = dict_in['chunk_size']
    chunk_filename_prefix = dict_in['chunk_filename_prefix']
    chunk_dest_dir = dict_in['chunk_dest_dir']
    #
    steps_done = 0
    while steps_done < original_n_steps:
        steps_remaining = original_n_steps - steps_done
        dict_in['n_steps'] = min(chunk_size, steps_remaining)
        # FIXME: modify SEED
        ith_chunk = steps_done / chunk_size
        dict_out = analyze_helper(table_data, dict_in)
        dict_in.update(dict_out)
        # write to hdfs
        chunk_filename = '%s_seed_%s_chunk_%s.pkl.gz' % (chunk_filename_prefix, original_SEED, ith_chunk)
        fu.pickle(dict_out, chunk_filename)
        HE.put_hdfs(None, chunk_filename, chunk_dest_dir)
        #
        steps_done += chunk_size
    chunk_filename = '%s_seed_%s_chunk_%s.pkl.gz' % (chunk_filename_prefix, original_SEED, 'FINAL')
    fu.pickle(dict_out, chunk_filename)
    HE.put_hdfs(None, chunk_filename, chunk_dest_dir)
    return dict_out
    
def time_analyze_helper(table_data, dict_in):
    start_dims = du.get_state_shape(dict_in['X_L'])
    with gu.Timer('time_analyze_helper', verbose=False) as timer:
        inner_ret_dict = analyze_helper(table_data, dict_in)
    end_dims = du.get_state_shape(inner_ret_dict['X_L'])
    T = table_data['T']
    table_shape = (len(T), len(T[0]))
    ret_dict = dict(
        table_shape=table_shape,
        start_dims=start_dims,
        end_dims=end_dims,
        elapsed_secs=timer.elapsed_secs,
        kernel_list=dict_in['kernel_list'],
        n_steps=dict_in['n_steps'],
        )
    return ret_dict

method_lookup = dict(
    initialize=initialize_helper,
    analyze=analyze_helper,
    time_analyze=time_analyze_helper,
    chunk_analyze=chunk_analyze_helper,
    )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--table_data_filename', type=str,
                        default=xu.default_table_data_filename)
    args = parser.parse_args()
    table_data_filename = args.table_data_filename
    table_data = fu.unpickle(table_data_filename)
    #
    from signal import signal, SIGPIPE, SIG_DFL 
    signal(SIGPIPE,SIG_DFL) 
    for line in sys.stdin:
        key, dict_in = xu.parse_hadoop_line(line)
        if dict_in is None:
            continue
        command = dict_in['command']
        method = method_lookup[command]
        ret_dict = method(table_data, dict_in)
        print key, ret_dict


import sys
import argparse
#
from pyspark import SparkContext
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.python_utils.general_utils as gu
import tabular_predDB.LocalEngine as LE


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
    SEED = dict_in['SEED']
    engine = LE.LocalEngine(SEED)
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=kernel_list,
                                          n_steps=n_steps, c=c, r=r)
    #
    ret_dict = dict(X_L=X_L, X_D=X_D)
    return ret_dict

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
    )

def process_line(line, table_data):
        key, dict_in = xu.parse_hadoop_line(line)
        if dict_in is None:
            return None, None
        command = dict_in['command']
        method = method_lookup[command]
        ret_dict = method(table_data, dict_in)
        return key, ret_dict

if __name__ == '__main__':
    pass

# read the files
table_data = fu.unpickle('table_data.pkl.gz')
with open('hadoop_input') as fh:
    lines = [line for line in fh]

sc = SparkContext("local", "Simple job")
broadcasted_table_data = sc.broadcast(table_data)
parallelized = sc.parallelize(lines)
map_result = parallelized.map(lambda line: process_line(line, broadcasted_table_data.value)).collect()

print map_result

#

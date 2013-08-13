import os
import csv
import argparse
import tempfile
#
import numpy
import itertools
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.hadoop_utils as hu
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.LocalEngine as LE
import tabular_predDB.HadoopEngine as HE
import tabular_predDB.cython_code.State as State
from collections import namedtuple
import time
import parse_convergence_results as pc


def generate_hadoop_dicts(convergence_run_parameters, args_dict):
    dict_to_write = dict(convergence_run_parameters)
    dict_to_write.update(args_dict)
    yield dict_to_write

def write_hadoop_input(input_filename, convergence_run_parameters, n_steps, block_size, SEED):
    # prep settings dictionary
    convergence_analyze_args_dict = xu.default_analyze_args_dict
    convergence_analyze_args_dict['command'] = 'convergence_analyze'
    convergence_analyze_args_dict['SEED'] = SEED
    convergence_analyze_args_dict['n_steps'] = n_steps
    convergence_analyze_args_dict['block_size'] = block_size
    
    with open(input_filename, 'a') as out_fh:
        dict_generator = generate_hadoop_dicts(convergence_run_parameters, convergence_analyze_args_dict)
        for dict_to_write in dict_generator:
            xu.write_hadoop_line(out_fh, key=dict_to_write['SEED'], dict_to_write=dict_to_write)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gen_seed', type=int, default=0)
    parser.add_argument('--n_steps', type=int, default=500)
    parser.add_argument('--num_chains', type=int, default=50)
    parser.add_argument('--block_size', type=int, default=20)
    parser.add_argument('-do_local', action='store_true')
    parser.add_argument('-do_remote', action='store_true')
    #
    args = parser.parse_args()
    gen_seed = args.gen_seed
    n_steps = args.n_steps
    do_local = args.do_local
    num_chains = args.num_chains
    do_remote = args.do_remote
    block_size = args.block_size

    script_filename = 'hadoop_line_processor.py'
    # some hadoop processing related settings
    # FIXME: need to make sure 'dir' argument exists
    temp_dir = tempfile.mkdtemp(prefix='convergence_analysis_',
                                dir='convergence_analysis')
    print 'using dir: %s' % temp_dir
    #
    table_data_filename = os.path.join(temp_dir, 'table_data.pkl.gz')
    input_filename = os.path.join(temp_dir, 'hadoop_input')
    output_filename = os.path.join(temp_dir, 'hadoop_output')
    output_path = os.path.join(temp_dir, 'output')  
    parsed_out_file = os.path.join(temp_dir, 'parsed_convergence_output.csv')

    # Hard code the parameter values for now

    num_rows_list = [200, 400, 1000]
    num_cols_list = [8, 16, 32]
    num_clusters_list = [5,10]
    num_splits_list = [2, 4]
    max_mean_list = [0.5, 1, 2]
    
#    num_rows_list = [200]
#    num_cols_list = [8]
#    num_clusters_list = [5]
#    num_splits_list = [2,4]
#    max_mean_list = [1]

    parameter_list = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list]

    count = -1
    # Iterate over the parameter values and write each run as a line in the hadoop_input file
    take_product_of = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list, max_mean_list]
    for num_rows, num_cols, num_clusters, num_splits, max_mean in itertools.product(*take_product_of):
        if numpy.mod(num_rows, num_clusters) == 0 and numpy.mod(num_cols,num_splits)==0:
          count = count + 1
          for chainindx in range(num_chains):
              convergence_run_parameters = dict(num_rows=num_rows, num_cols=num_cols,
                      num_views=num_splits, num_clusters=num_clusters, max_mean=max_mean,
                      n_test=100,
                      init_seed=chainindx)
              write_hadoop_input(input_filename, convergence_run_parameters,  n_steps, block_size,
                      SEED=count)

    n_tasks = len(num_rows_list)*len(num_cols_list)*len(num_clusters_list)*len(num_splits_list)*len(max_mean_list)*num_chains
    # Create a dummy table data file
    table_data=dict(T=[],M_c=[],X_L=[],X_D=[])
    fu.pickle(table_data, table_data_filename)

    if do_local:
        xu.run_script_local(input_filename, script_filename, output_filename, table_data_filename)
        print 'Local Engine for automated convergence runs has not been completely implemented/tested'
    elif do_remote:
        hadoop_engine = HE.HadoopEngine(output_path=output_path,
                                        input_filename=input_filename,
                                        table_data_filename=table_data_filename,
                                        )
        xu.write_support_files(table_data, hadoop_engine.table_data_filename,
                              dict(command='convergence_analyze'), hadoop_engine.command_dict_filename)
        hadoop_engine.send_hadoop_command(n_tasks=n_tasks)
        was_successful = hadoop_engine.get_hadoop_results()
        if was_successful:
            hu.copy_hadoop_output(hadoop_engine.output_path, output_filename)
            pc.parse_to_csv(output_filename,parsed_out_file)
        else:
            print 'remote hadoop job NOT successful'
    else:
        # print what the command would be
        hadoop_engine = HE.HadoopEngine(output_path=output_path,
                input_filename=input_filename,
                table_data_filename=table_data_filename,
                )
        cmd_str = hu.create_hadoop_cmd_str(
                hadoop_engine.hdfs_uri, hadoop_engine.hdfs_dir, hadoop_engine.jobtracker_uri,
                hadoop_engine.which_engine_binary, hadoop_engine.which_hadoop_binary,
                hadoop_engine.which_hadoop_jar,
                hadoop_engine.input_filename, hadoop_engine.table_data_filename,
                hadoop_engine.command_dict_filename, hadoop_engine.output_path,
                n_tasks, hadoop_engine.one_map_task_per_line)
        print cmd_str

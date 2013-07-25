import os
import csv
import argparse
import tempfile
#
import numpy
import itertools
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.LocalEngine as LE
import tabular_predDB.HadoopEngine as HE
import tabular_predDB.cython_code.State as State
from collections import namedtuple
import time
import pdb

def generate_hadoop_dicts(timing_run_parameters, args_dict):
    dict_to_write = dict(timing_run_parameters)
    dict_to_write.update(args_dict)
    yield dict_to_write

def write_hadoop_input(input_filename, timing_run_parameters, n_steps, block_size, SEED):
    # prep settings dictionary
    convergence_analyze_args_dict = xu.default_analyze_args_dict
    convergence_analyze_args_dict['command'] = 'convergence_analyze'
    convergence_analyze_args_dict['SEED'] = SEED
    convergence_analyze_args_dict['n_steps'] = n_steps
    convergence_analyze_args_dict['block_size'] = block_size
    
    with open(input_filename, 'a') as out_fh:
        dict_generator = generate_hadoop_dicts(timing_run_parameters, convergence_analyze_args_dict)
        for dict_to_write in dict_generator:
            xu.write_hadoop_line(out_fh, key=dict_to_write['SEED'], dict_to_write=dict_to_write)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gen_seed', type=int, default=0)
    parser.add_argument('--n_steps', type=int, default=100)
    parser.add_argument('--num_chains', type=int, default=20)
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
    temp_dir = tempfile.mkdtemp(prefix='convergence_analysis_',
                                dir='convergence_analysis')
    print 'using dir: %s' % temp_dir
    #
    table_data_filename = os.path.join(temp_dir, 'table_data.pkl.gz')
    input_filename = os.path.join(temp_dir, 'hadoop_input')
    output_filename = os.path.join(temp_dir, 'hadoop_output')
    output_path = os.path.join(temp_dir, 'output')  
    parsed_out_file = os.path.join(temp_dir, 'parsed_output.csv')

    # Hard code the parameter values for now

    #num_rows_list = [100, 400, 1000, 4000, 10000]
    #num_cols_list = [4, 8, 16, 24, 32]
    #num_clusters_list = [10, 20, 30, 40, 50]
    #num_splits_list = [1, 2, 3, 4, 5]
    
    num_rows_list = [200, 400]
    num_cols_list = [8]
    num_clusters_list = [5, 10]
    num_splits_list = [2,4]

    parameter_list = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list]

    count = -1
    # Iterate over the parameter values and write each run as a line in the hadoop_input file
    take_product_of = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list]
    for num_rows, num_cols, num_clusters, num_splits in itertools.product(*take_product_of):
        if numpy.mod(num_rows, num_clusters) == 0 and numpy.mod(num_cols,num_splits)==0:
          count = count + 1
          for chainindx in range(num_chains):
              timing_run_parameters = dict(num_rows=num_rows, num_cols=num_cols, \
                                           num_views=num_splits, num_clusters=num_clusters, init_seed = chainindx)
              write_hadoop_input(input_filename, timing_run_parameters,  n_steps, block_size, SEED=count)

    n_tasks = len(num_rows_list)*len(num_cols_list)*len(num_clusters_list)*len(num_splits_list)*num_chains
    # Create a dummy table data file
    table_data=dict(T=[],M_c=[],X_L=[],X_D=[])
    xu.pickle_table_data(table_data, table_data_filename)

    if do_local:
        xu.run_script_local(input_filename, script_filename, output_filename, table_data_filename)
        print 'Local Engine for automated timing runs has not been completely implemented/tested'
    elif do_remote:
        hadoop_engine = HE.HadoopEngine(output_path=output_path,
                                        input_filename=input_filename,
                                        table_data_filename=table_data_filename,
                                        )
	
        was_successful = HE.send_hadoop_command(hadoop_engine,
                                                table_data_filename,
                                                input_filename,
                                                output_path, n_tasks=n_tasks)
        if was_successful:
            #HE.read_hadoop_output(output_path, output_filename)
	    hadoop_output_filename = HE.get_hadoop_output_filename(output_path)
            cmd_str = 'cp %s %s' % (hadoop_output_filename, output_filename) 
	    os.system(cmd_str)

        else:
            print 'remote hadoop job NOT successful'
    else:
        hadoop_engine = HE.HadoopEngine()
        # print what the command would be
        print HE.create_hadoop_cmd_str(hadoop_engine, n_tasks=n_tasks)

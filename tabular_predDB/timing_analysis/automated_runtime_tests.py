import os, csv
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
import parse_timing
from collections import namedtuple

def generate_hadoop_dicts(which_kernels, timing_run_parameters, args_dict):
    for which_kernel in which_kernels:
        kernel_list = (which_kernel, )
        dict_to_write = dict(timing_run_parameters)
        dict_to_write.update(args_dict)
        # must write kernel_list after update
        dict_to_write['kernel_list'] = kernel_list
        yield dict_to_write

def write_hadoop_input(input_filename, timing_run_parameters, n_steps, SEED):
    # prep settings dictionary
    time_analyze_args_dict = xu.default_analyze_args_dict
    time_analyze_args_dict['command'] = 'time_analyze'
    time_analyze_args_dict['SEED'] = SEED
    time_analyze_args_dict['n_steps'] = n_steps
    # one kernel per line
    all_kernels = State.transition_name_to_method_name_and_args.keys()
    with open(input_filename, 'a') as out_fh:
        dict_generator = generate_hadoop_dicts(all_kernels,timing_run_parameters, time_analyze_args_dict)
        for dict_to_write in dict_generator:
            xu.write_hadoop_line(out_fh, key=dict_to_write['SEED'], dict_to_write=dict_to_write)

def find_regression_coeff(filename, parameter_list):

    # Find regression coefficients from the times stored in the parsed csv files
    num_cols = 20
    # Read the csv file
    with open(filename) as fh:
        csv_reader = csv.reader(fh)
        header = csv_reader.next()[:num_cols]
        timing_rows = [row[:num_cols] for row in csv_reader]

    
    num_rows_list = parameter_list[0]
    num_cols_list = parameter_list[1]
    num_clusters_list = parameter_list[2]
    num_views_list = parameter_list[3]

     # Iterate over the parameter values and finding matching indices in the timing data
    take_product_of = [num_rows_list, num_cols_list, num_clusters_list, num_views_list]
    count = -1
    a_matrix = numpy.ones((len(num_rows_list)*len(num_cols_list)*len(num_clusters_list)*len(num_views_list), 5))
    b_matrix = numpy.zeros((len(num_rows_list)*len(num_cols_list)*len(num_clusters_list)*len(num_views_list), 1))

    times_only = numpy.asarray([float(timing_rows[i][4]) for i in range(len(timing_rows))])
    #pdb.set_trace()
    for num_rows, num_cols, num_clusters, num_views in itertools.product(*take_product_of):
        matchindx = [i for i in range(len(timing_rows)) if timing_rows[i][0] == str(num_rows) and \
                         timing_rows[i][1]== str(num_cols) and \
                         timing_rows[i][2]== str(num_clusters) and \
                         timing_rows[i][3]== str(num_views)]
        if matchindx != []:
          count = count + 1
          a_matrix[count,1] = num_rows
          a_matrix[count,2] = num_cols*num_clusters
          a_matrix[count,3] = num_rows*num_cols*num_clusters
          a_matrix[count,4] = num_views*num_rows*num_cols
          b_matrix[count] = numpy.sum(times_only[matchindx]) 
        
    x, j1, j2, j3 = numpy.linalg.lstsq(a_matrix,b_matrix)


    return x    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gen_seed', type=int, default=0)
    parser.add_argument('--n_steps', type=int, default=10)
    parser.add_argument('-do_local', action='store_true')
    parser.add_argument('-do_remote', action='store_true')
    #
    args = parser.parse_args()
    gen_seed = args.gen_seed
    n_steps = args.n_steps
    do_local = args.do_local
    do_remote = args.do_remote

    script_filename = 'hadoop_line_processor.py'
    # some hadoop processing related settings
    temp_dir = tempfile.mkdtemp(prefix='runtime_analysis_',
                                dir='runtime_analysis')
    print 'using dir: %s' % temp_dir
    #
    table_data_filename = os.path.join(temp_dir, 'table_data.pkl.gz')
    input_filename = os.path.join(temp_dir, 'hadoop_input')
    output_filename = os.path.join(temp_dir, 'hadoop_output')
    output_path = os.path.join(temp_dir, 'output')
    

    # Hard code the parameter values for now

    #num_rows_list = [100, 400, 1000, 4000, 10000]
    #num_cols_list = [4, 8, 16, 24, 32]
    #num_clusters_list = [10, 20, 30, 40, 50]
    #num_splits_list = [1, 2, 3, 4, 5]
    
    num_rows_list = [100, 400, 1000]
    num_cols_list = [8, 16, 24, 64]
    num_clusters_list = [5, 10, 20, 40, 50]
    num_splits_list = [1,8,16]

    parameter_list = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list]

    # Iterate over the parameter values and write each run as a line in the hadoop_input file
    take_product_of = [num_rows_list, num_cols_list, num_clusters_list, num_splits_list]
    for num_rows, num_cols, num_clusters, num_splits \
            in itertools.product(*take_product_of):
        if numpy.mod(num_rows, num_clusters) == 0 and numpy.mod(num_cols,num_splits)==0:
          timing_run_parameters = dict(num_rows=num_rows, num_cols=num_cols, num_views=num_splits, num_clusters=num_clusters)
          write_hadoop_input(input_filename, timing_run_parameters,  n_steps, SEED=gen_seed)

    n_tasks = len(num_rows_list)*len(num_cols_list)*len(num_clusters_list)*len(num_splits_list)*5
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
            parse_timing.parse_timing_to_csv(output_filename)
            coeff_list = find_regression_coeff(output_filename, parameter_list)

        else:
            print 'remote hadoop job NOT successful'
    else:
        hadoop_engine = HE.HadoopEngine()
        # print what the command would be
        print HE.create_hadoop_cmd_str(hadoop_engine, n_tasks=n_tasks)

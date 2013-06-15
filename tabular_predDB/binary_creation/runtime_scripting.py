import argparse
#
import numpy
import pylab
pylab.ion()
pylab.show()
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.general_utils as gu
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.LocalEngine as LE
import tabular_predDB.cython_code.State as State


def get_generative_clustering(M_c, M_r, T,
                              data_inverse_permutation_indices,
                              num_clusters, num_views):
    # NOTE: this function only works because State.p_State doesn't use
    #       column_component_suffstats
    num_rows = len(T)
    num_cols = len(T[0])
    X_D_helper = numpy.repeat(range(num_clusters), (num_rows / num_clusters))
    gen_X_D = [
        X_D_helper[numpy.argsort(data_inverse_permutation_index)]
        for data_inverse_permutation_index in data_inverse_permutation_indices
        ]
    gen_X_L_assignments = numpy.repeat(range(num_views), (num_cols / num_views))
    # initialize to generate an X_L to manipulate
    local_engine = LE.LocalEngine()
    M_c, M_r, bad_X_L, bad_X_D = local_engine.initialize(M_c, M_r, T,
                                                         initialization='apart')
    bad_X_L['column_partition']['assignments'] = gen_X_L_assignments
    # manually constrcut state in in generative configuration
    state = State.p_State(M_c, T, bad_X_L, gen_X_D)
    gen_X_L = state.get_X_L()
    gen_X_D = state.get_X_D()
    # run inference on hyperparameters to leave them in a reasonable state
    kernel_list = (
        'row_partition_hyperparameters',
        'column_hyperparameters',
        'column_partition_hyperparameter',
        )
    gen_X_L, gen_X_D = local_engine.analyze(M_c, T, gen_X_L, gen_X_D, n_steps=1,
                                            kernel_list=kernel_list)
    #
    return gen_X_L, gen_X_D

def generate_clean_state(gen_seed, num_clusters,
                         num_cols, num_rows, num_splits,
                         max_mean=10, max_std=1,
                         plot=False):
    # generate the data
    T, M_r, M_c, data_inverse_permutation_indices = \
        du.gen_factorial_data_objects(gen_seed, num_clusters,
                                      num_cols, num_rows, num_splits,
                                      max_mean=10, max_std=1,
                                      send_data_inverse_permutation_indices=True)
    # recover generative clustering
    X_L, X_D = get_generative_clustering(M_c, M_r, T,
                                         data_inverse_permutation_indices,
                                         num_clusters, num_splits)
    if plot:
        T_array = numpy.array(T)
        pu.plot_views(T_array, X_D, X_L, M_c)
    return T, M_c, M_r, X_L, X_D


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gen_seed', type=int, default=0)
    parser.add_argument('--num_clusters', type=int, default=20)
    parser.add_argument('--num_rows', type=int, default=1000)
    parser.add_argument('--num_cols', type=int, default=20)
    parser.add_argument('--num_splits', type=int, default=2)
    parser.add_argument('--max_std', type=float, default=.001)
    parser.add_argument('--n_steps', type=int, default=10)
    #
    args = parser.parse_args()
    gen_seed = args.gen_seed
    num_clusters = args.num_clusters
    num_cols = args.num_cols
    num_rows = args.num_rows
    num_splits = args.num_splits
    max_std = args.max_std
    n_steps = args.n_steps

    # generate data
    T, M_c, M_r, X_L, X_D = generate_clean_state(gen_seed,
                                                 num_clusters,
                                                 num_cols, num_rows,
                                                 num_splits,
                                                 max_mean=10, max_std=1)

    # some hadoop processing related settings
    table_data_filename = 'table_data.pkl.gz'
    hadoop_input_filename = 'hadoop_input'
    script_filename = 'hadoop_line_processor.py'
    hadoop_output_filename = 'hadoop_output'
    SEED = 0

    # prep settings dictionary
    time_analyze_args_dict = xu.default_analyze_args_dict
    time_analyze_args_dict['SEED'] = SEED
    time_analyze_args_dict['command'] = 'time_analyze'
    time_analyze_args_dict['n_steps'] = n_steps

    # write table_data and hadoop input
    table_data = dict(M_c=M_c, M_r=M_r, T=T)
    xu.pickle_table_data(table_data, table_data_filename)
    # one kernel per line
    all_kernels = State.transition_name_to_method_name_and_args.keys()
    with open(hadoop_input_filename, 'w') as out_fh:
        for which_kernel in all_kernels:
            kernel_list = (which_kernel, )
            dict_to_write = dict(X_L=X_L, X_D=X_D)
            dict_to_write.update(time_analyze_args_dict)
            # must write kernel_list after update
            dict_to_write['kernel_list'] = kernel_list
            xu.write_hadoop_line(out_fh, key=dict_to_write['SEED'], dict_to_write=dict_to_write)

    # actually run
    xu.run_script_local(hadoop_input_filename, script_filename, hadoop_output_filename)

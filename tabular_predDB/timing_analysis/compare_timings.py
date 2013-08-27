import os
import csv
import collections


def timing_row_to_config_and_runtime(header, row):
    row_dict = dict(zip(header,row))
    config_tuple = tuple([
            row_dict[column_name]
            for column_name in config_column_names
            ])
    which_kernel = row_dict['which_kernel']
    runtime = float(row_dict['time_per_step'])
    return (config_tuple, which_kernel), runtime

def reparse_parsed_timing_csv(filename):
    with open(filename) as fh:
        csv_reader = csv.reader(fh)
        header = csv_reader.next()
        reparsed_dict = dict(
                timing_row_to_config_and_runtime(header, row)
                for row in csv_reader
                )
    return reparsed_dict

def filter_dict(in_dict, key_filter):
    out_dict = dict()
    for key, value in in_dict.iteritems():
        if key_filter(key):
            out_dict[key] = value
    return out_dict

def get_config(key):
    return key[0]

def get_which_kernel(key):
    return key[1]

def get_config_filter(column_name, filter_func):
    which_index = config_column_names.index(column_name)
    return lambda key: filter_func(get_config(key)[which_index])

def get_key_intersect_dict(dict_1, dict_2):
    intersect_keys = set(dict_1.keys()).intersection(dict_2)
    intersect_dict = dict(
            (key, (dict_1[key], dict_2[key]))
            for key in intersect_keys
            )
    return intersect_dict

def get_complete_configs_dict(in_dict):
    config_kernel_counter = collections.Counter(map(get_config, in_dict.keys()))
    complete_configs = set([
            config
            for config, count in config_kernel_counter.iteritems()
            if count == 5
            ])
    is_complete_config = lambda key: get_config(key) in complete_configs
    complete_configs_dict = filter_dict(in_dict, is_complete_config)
    return complete_configs_dict

timing_div = lambda timing_tuple: timing_tuple[0] / timing_tuple[1]
get_4_digits_str = lambda el: '%.4f' % el

config_column_names = ['num_rows', 'num_cols', 'num_clusters', 'num_views']
which_kernels = ['row_partition_hyperparameters',
    'column_partition_hyperparameter',
    'column_partition_assignments',
    'row_partition_assignments',
    'column_hyperparameters',
    ]


if __name__ == '__main__':
    import argparse
    #
    parser = argparse.ArgumentParser()
    parser.add_argument('timing_filename_1', type=str)
    parser.add_argument('timing_filename_2', type=str)
    args = parser.parse_args()
    #
    timing_filename_1 = args.timing_filename_1
    timing_filename_2 = args.timing_filename_2
#    timing_filename_1 = 'Work/runtime_analysis_W_Y10u_parsed_output.csv'
#    timing_filename_2 = 'Work/runtime_analysis_v96OCK_parsed_output.csv'
    assert(os.path.isfile(timing_filename_1))
    assert(os.path.isfile(timing_filename_2))

    reparsed_dict_1 = reparse_parsed_timing_csv(timing_filename_1)
    reparsed_dict_2 = reparse_parsed_timing_csv(timing_filename_2)
    intersect_dict = get_key_intersect_dict(reparsed_dict_1, reparsed_dict_2)
    complete_configs_dict = get_complete_configs_dict(intersect_dict)
    #
    for which_kernel in which_kernels:
        comparison_dict = complete_configs_dict.copy()
        which_filters = [
                get_config_filter('num_rows', lambda config: int(config) >= 1000),
                get_config_filter('num_cols', lambda config: int(config) >= 32),
                lambda key: get_which_kernel(key) == which_kernel,
                ]
        for which_filter in which_filters:
            comparison_dict = filter_dict(comparison_dict, which_filter)
        cmp_timing_tuples = lambda tuple1, tuple2: \
            cmp(tuple1[1], tuple2[1])
        for key, value in sorted(comparison_dict.iteritems(), cmp=cmp_timing_tuples):
            time_tuple = map(get_4_digits_str, value)
            print key, time_tuple, get_4_digits_str(timing_div(value))

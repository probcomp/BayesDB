import tabular_predDB.binary_creation.xnet_utils as xu


# settings
filename = '../web_resources/data/dha.csv'
script_name = 'hadoop_line_processor.py'
#
table_data_filename = xu.default_table_data_filename
initialize_input_filename = 'initialize_input'
initialize_output_filename = 'initialize_output'
analyze_input_filename = 'analyze_input'
analyze_output_filename = 'analyze_output'

# set up
table_data = xu.pickle_table_data(filename, table_data_filename)

# create initialize input
with open(initialize_input_filename, 'w') as in_fh:
    for SEED in range(5):
        out_dict = xu.default_initialize_args_dict.copy()
        out_dict['SEED'] = SEED
        xu.write_hadoop_line(in_fh, SEED, out_dict)

# initialize
xu.run_script_local(initialize_input_filename, script_name,
                    initialize_output_filename)

# read initialization output, write analyze input
analyze_args_dict = xu.defautl_analyze_args_dict
xu.link_initialize_to_analyze(initialize_output_filename,
                              analyze_input_filename,
                              analyze_args_dict)

# analyze
xu.run_script_local(analyze_input_filename, script_name,
                    analyze_output_filename)

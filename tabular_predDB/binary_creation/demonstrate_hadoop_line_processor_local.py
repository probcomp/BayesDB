import tabular_predDB.python_utils.xnet_utils as xu


# settings
n_chains = 20
n_steps = 20
#
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
xu.write_initialization_files(initialize_input_filename, n_chains)

# initialize
xu.run_script_local(initialize_input_filename, script_name,
                    initialize_output_filename)

# read initialization output, write analyze input
analyze_args_dict = xu.default_analyze_args_dict
analyze_args_dict['n_steps'] = n_steps
xu.link_initialize_to_analyze(initialize_output_filename,
                              analyze_input_filename,
                              analyze_args_dict)

# analyze
xu.run_script_local(analyze_input_filename, script_name,
                    analyze_output_filename)

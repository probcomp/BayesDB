import os
#
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.settings as S


# settings
n_chains = 20
n_steps = 20
#
filename = os.path.join(S.path.web_resources_data_dir, 'dha_small.csv')
script_name = 'hadoop_line_processor.py'
#
table_data_filename = xu.default_table_data_filename
initialize_input_filename = 'initialize_input'
initialize_output_filename = 'initialize_output'
initialize_args_dict = xu.default_initialize_args_dict
analyze_input_filename = 'analyze_input'
analyze_output_filename = 'analyze_output'
analyze_args_dict = xu.default_analyze_args_dict

# set up
table_data = xu.pickle_table_data(filename, table_data_filename)

# create initialize input
xu.write_initialization_files(initialize_input_filename,
                              initialize_args_dict=initialize_args_dict,
                              n_chains=n_chains)

# initialize
xu.run_script_local(initialize_input_filename, script_name,
                    initialize_output_filename)

# read initialization output, write analyze input
analyze_args_dict['n_steps'] = n_steps
xu.link_initialize_to_analyze(initialize_output_filename,
                              analyze_input_filename,
                              analyze_args_dict)

# analyze
xu.run_script_local(analyze_input_filename, script_name,
                    analyze_output_filename)

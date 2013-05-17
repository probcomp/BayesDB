import os
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.binary_creation.hadoop_line_processor as hlp


# settings
filename = '../web_resources/data/dha.csv'
script_name = 'hadoop_line_processor.py'
#
table_data_filename = 'table_data.pkl.gz'
initialize_input_filename = 'initialize_input'
initialize_output_filename = 'initialize_output'
analyze_input_filename = 'analyze_input'
analyze_output_filename = 'analyze_output'

# set up
T, M_r, M_c = du.read_model_data_from_csv(filename, gen_seed=0)
table_data = dict(T=T, M_r=M_r, M_c=M_c)
fu.pickle(table_data, table_data_filename)

# create initialize input
command = 'initialize'
initialization = 'from_the_prior'
with open(initialize_input_filename, 'w') as fh:
    for SEED in range(5):
        out_dict = dict(command=command, initialization=initialization, SEED=SEED)
        fh.write(' '.join(map(str, [SEED, out_dict])))
        fh.write('\n')

# initialize
cmd_str = 'cat %s | python %s > %s'
cmd_str %= (initialize_input_filename, script_name, initialize_output_filename)
os.system(cmd_str)

def set_to_analyze(dict_in, SEED):
    dict_in['command'] = 'analyze'
    dict_in['kernel_list'] = ()
    dict_in['n_steps'] = 1
    dict_in['c'] = ()
    dict_in['r'] = ()
    dict_in['SEED'] = SEED
    return dict_in

# read initialization output, write analyze input
with open(initialize_output_filename) as in_fh:
    with open(analyze_input_filename, 'w') as out_fh:
        for line in in_fh:
            key, dict_in = hlp.parse_line(line)
            dict_in = set_to_analyze(dict_in, int(key))
            out_fh.write(' '.join(map(str, [key, dict_in])))
            out_fh.write('\n')

# analyze
cmd_str = 'cat %s | python %s > %s'
cmd_str %= (analyze_input_filename, script_name, analyze_output_filename)
os.system(cmd_str)

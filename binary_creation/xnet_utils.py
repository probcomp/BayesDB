import os
import re
import argparse
#
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.data_utils as du


default_table_data_filename = 'table_data.pkl.gz'

default_initialize_args_dict = dict(
    command='initialize',
    initialization='from_the_prior',
    )

default_analyze_args_dict = dict(
    command='analyze',
    kernel_list=(),
    n_steps=1,
    c=(),
    r=(),
    )

# read the data, create metadata
def pickle_table_data(in_filename, pkl_filename):
    T, M_r, M_c = du.read_model_data_from_csv(in_filename, gen_seed=0)
    table_data = dict(T=T, M_r=M_r, M_c=M_c)
    fu.pickle(table_data, pkl_filename)
    return table_data

# cat the data into the script, as hadoop would
def run_script_local(infile, script_name, outfile):
    cmd_str = 'cat %s | python %s > %s'
    cmd_str %= (infile, script_name, outfile)
    os.system(cmd_str)
    return

def write_hadoop_line(fh, key, dict_to_write):
    fh.write(' '.join(map(str, [key, dict_to_write])))
    fh.write('\n')
    return

line_re = '(\d+)\s+(.*)'
pattern = re.compile(line_re)
def parse_hadoop_line(line):
    line = line.strip()
    match = pattern.match(line)
    key, dict_in = None, None
    if match:
        key, dict_in_str = match.groups()
        dict_in = eval(dict_in_str)
    return key, dict_in

# read initialization output, write analyze input
def link_initialize_to_analyze(initialize_output_filename,
                               analyze_input_filename,
                               analyze_args_dict=default_analyze_args_dict):
    with open(initialize_output_filename) as in_fh:
        with open(analyze_input_filename, 'w') as out_fh:
            for line in in_fh:
                key, dict_in = parse_hadoop_line(line)
                dict_in.update(analyze_args_dict)
                dict_in['SEED'] = int(key)
                write_hadoop_line(out_fh, key, dict_in)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--initialize_output_filename',
                        default='initialize_output', type=str)
    parser.add_argument('--analyze_input_filename',
                        default='analyze_input', type=str)

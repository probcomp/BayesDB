import os
import re
import argparse
import cPickle
#
import tabular_predDB.settings as S
from tabular_predDB.settings import Hadoop as hs
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.data_utils as du


default_table_data_filename = hs.default_table_data_filename
default_table_filename = hs.default_table_filename
default_analyze_args_dict = hs.default_analyze_args_dict.copy()
default_initialize_args_dict = hs.default_initialize_args_dict.copy()


# read the data, create metadata
def pickle_table_data(in_filename_or_dict, pkl_filename):
    table_data = None
    if isinstance(in_filename_or_dict, str):
        T, M_r, M_c = du.read_model_data_from_csv(in_filename_or_dict, gen_seed=0)
        table_data = dict(T=T, M_r=M_r, M_c=M_c)
    else:
        table_data = in_filename_or_dict
    fu.pickle(table_data, pkl_filename)
    return table_data

# cat the data into the script, as hadoop would
def run_script_local(infile, script_name, outfile):
    cmd_str = 'cat %s | python %s > %s'
    cmd_str %= (infile, script_name, outfile)
    os.system(cmd_str)
    return

newline_escape = 'NEWLINE_ESCAPE'
def my_dumps(in_object):
    unescaped_str = cPickle.dumps(in_object)
    escaped_str = unescaped_str.replace('\n', newline_escape)
    return escaped_str
def my_loads(escaped_str):
    unescaped_str = escaped_str.replace(newline_escape, '\n')
    out_object = cPickle.loads(unescaped_str)
    return out_object

def write_hadoop_line(fh, key, dict_to_write):
    escaped_str = my_dumps(dict_to_write)
    fh.write(str(key) + ' ')
    fh.write(escaped_str)
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
        try:
          dict_in = my_loads(dict_in_str)
        except Exception, e:
          # for parsing new NLineInputFormat
          match = pattern.match(dict_in_str)
          if match is None:
            print 'OMG: ' + dict_in_str[:50]
          key, dict_in_str = match.groups()
          dict_in = my_loads(dict_in_str)
    return key, dict_in

def write_initialization_files(initialize_input_filename,
                               initialize_args_dict=None,
                               n_chains=10):
    if initialize_args_dict is None:
        initialize_args_dict = default_initialize_args_dict.copy()
    with open(initialize_input_filename, 'w') as out_fh:
        for SEED in range(n_chains):
            out_dict = initialize_args_dict.copy()
            out_dict['SEED'] = SEED
            write_hadoop_line(out_fh, SEED, out_dict)
    return

# read initialization output, write analyze input
def link_initialize_to_analyze(initialize_output_filename,
                               analyze_input_filename,
                               analyze_args_dict=None):
    if analyze_args_dict is None:
        analyze_args_dict = default_analyze_args_dict.copy()
    num_lines = 0
    with open(initialize_output_filename) as in_fh:
        with open(analyze_input_filename, 'w') as out_fh:
            for line in in_fh:
                num_lines += 1
                key, dict_in = parse_hadoop_line(line)
                dict_in.update(analyze_args_dict)
                dict_in['SEED'] = int(key)
                write_hadoop_line(out_fh, key, dict_in)
    return num_lines

def get_is_multistate(X_L, X_D):
    if isinstance(X_L, (list, tuple)):
        assert isinstance(X_D, (list, tuple))
        return True
    else:
        return False

def get_is_vpn_connected():
    # cmd_str = 'ifconfig | grep tun'
    cmd_str = 'ping -W 2 -c 1 10.1.90.10'
    lines = [line for line in os.popen(cmd_str)]
    is_vpn_connected = False
    if len(lines) != 0:
        is_vpn_connected = True
    return is_vpn_connected

def assert_vpn_is_connected():
    is_vpn_connected = get_is_vpn_connected()
    assert is_vpn_connected
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('do_what', type=str)
    parser.add_argument('--hadoop_filename', type=str, default=None)
    parser.add_argument('--table_filename',
        default=default_table_filename, type=str)
    parser.add_argument('--pkl_filename',
                        default=default_table_data_filename, type=str)
    parser.add_argument('--initialize_input_filename',
                        default='initialize_input', type=str)
    parser.add_argument('--initialize_output_filename',
                        default='initialize_output', type=str)
    parser.add_argument('--analyze_input_filename',
                        default='analyze_input', type=str)
    parser.add_argument('--n_steps', default=1, type=int)
    parser.add_argument('--n_chains', default=1, type=int)
    args = parser.parse_args()
    #
    do_what = args.do_what
    hadoop_filename = args.hadoop_filename
    table_filename = args.table_filename
    pkl_filename = args.pkl_filename
    initialize_input_filename = args.initialize_input_filename
    initialize_output_filename = args.initialize_output_filename
    analyze_input_filename = args.analyze_input_filename
    n_steps = args.n_steps
    n_chains = args.n_chains


    if do_what == 'pickle_table_data':
        pickle_table_data(table_filename, pkl_filename)
    elif do_what == 'write_initialization_files':
        write_initialization_files(initialize_input_filename, n_chains)
    elif do_what == 'link_initialize_to_analyze':
        analyze_args_dict = default_analyze_args_dict.copy()
        analyze_args_dict['n_steps'] = n_steps
        link_initialize_to_analyze(initialize_output_filename,
                                   analyze_input_filename,
                                   analyze_args_dict)
    elif do_what == 'assert_vpn_is_connected':
        assert_vpn_is_connected()
    elif do_what == 'parse_hadoop_lines':
        assert hadoop_filename is not None
        parsed_lines = []
        with open(hadoop_filename) as fh:
            for line in fh:
                parsed_lines.append(parse_hadoop_line(line))
                print len(parsed_lines)
        if pkl_filename != default_table_data_filename:
            fu.pickle(parsed_lines, pkl_filename)
    else:
        print 'uknown do_what: %s' % do_what

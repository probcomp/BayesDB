#!/opt/anaconda/bin/python

#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import sys
import re
#
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.jsonrpc_http.Engine as E


# settings
filename = 'table_data.pkl.gz'
line_re = '(\d+)\s+(.*)'

pattern = re.compile(line_re)
def parse_line(line):
    line = line.strip()
    match = pattern.match(line)
    key, dict_in = None, None
    if match:
        key, dict_in_str = match.groups()
        dict_in = eval(dict_in_str)
    return key, dict_in

def initialize_helper(table_data, dict_in):
    M_c = table_data['M_c']
    M_r = table_data['M_r']
    T = table_data['T']
    initialization = dict_in['initialization']
    SEED = dict_in['SEED']
    engine = E.Engine(SEED)
    M_c_prime, M_r_prime, X_L, X_D = \
               engine.initialize(M_c, M_r, T, initialization=initialization)
    #
    ret_dict = dict(X_L=X_L, X_D=X_D)
    return ret_dict

def analyze_helper(table_data, dict_in):
    M_c = table_data['M_c']
    T = table_data['T']
    X_L = dict_in['X_L']
    X_D = dict_in['X_D']
    kernel_list = dict_in['kernel_list']
    n_steps = dict_in['n_steps']
    c = dict_in['c']
    r = dict_in['r']
    SEED = dict_in['SEED']
    engine = E.Engine(SEED)
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=(),
                                          n_steps=n_steps, c=c, r=r)
    #
    ret_dict = dict(X_L=X_L, X_D=X_D)
    return ret_dict

method_lookup = dict(
    initialize=initialize_helper,
    analyze=analyze_helper,
    )


if __name__ == '__main__':
    table_data = fu.unpickle(filename)
    #
    for line in sys.stdin:
        key, dict_in = parse_line(line)
        if dict_in is None:
            continue
        command = dict_in['command']
        method = method_lookup[command]
        ret_dict = method(table_data, dict_in)
        print key, ret_dict

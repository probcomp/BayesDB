import time
import requests
import json
#
import numpy
#
import Engine as E


# settings
URI = 'http://localhost:8007'
id = 0


# helper functions
def create_message(method_name, params):
    global id
    id += 1
    message = {
        'jsonrpc': '2.0',
        'method': method_name,
        'params': params,
        'id': str(id),
        }
    return json.dumps(message)

def call_and_print(method_name, args_dict):
    message = create_message(method_name, args_dict)
    print 'trying message:', message
    r = requests.put(URI, data=message)
    r.raise_for_status()
    out = json.loads(r.content)
    print out
    print
    if isinstance(out, dict) and 'result' in out:
        return out['result']
    else:
        # error?
        return out

T_dim = (3, 4)
T = (numpy.arange(numpy.prod(T_dim)).reshape(T_dim) * 1.0).tolist()

# non-stub functions
non_stub = set(['initialize', 'initialize_and_analyze', 'analyze'])
#
method_name = 'initialize'
args_dict = dict()
args_dict['M_c'] = 'M_c'
args_dict['M_r'] = 'M_r'
args_dict['i'] = ''
args_dict['T'] = T
out = call_and_print(method_name, args_dict)
time.sleep(1)
#
method_name = 'initialize_and_analyze'
args_dict = dict()
args_dict['n_steps'] = 10
args_dict['SEED'] = 0
args_dict['T'] = T
out = call_and_print(method_name, args_dict)
time.sleep(1)


X_L_prime, X_D_prime = out
method_name = 'analyze'
args_dict = dict()
args_dict['M_c'] = 'M_c'
args_dict['T'] = T
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['kernel_list'] = 'kernel_list'
args_dict['n_steps'] = 2
args_dict['c'] = 'c'
args_dict['r'] = 'r'
args_dict['max_iterations'] = 'max_iterations'
args_dict['max_time'] = 'max_time'
out = call_and_print(method_name, args_dict)
time.sleep(1)

# programmatically call all the other method calls
method_name_to_args = E.get_method_name_to_args()
for method_name, arg_str_list in method_name_to_args.iteritems():
    if method_name in non_stub:
        print 'skipping non-stub method:', method_name
        print
        continue
    args_dict = dict(zip(arg_str_list, arg_str_list))
    call_and_print(method_name, args_dict)
    time.sleep(1)

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
    print json.loads(r.content)
    print

non_stub = set(['initialize', 'initialize_and_analyze'])
# non-stub functions
method_name = 'initialize'
args_dict = dict()
args_dict['M_c'] = 'M_c'
args_dict['M_r'] = 'M_r'
args_dict['i'] = ''
T_dim = (3, 4)
T = (numpy.arange(numpy.prod(T_dim)).reshape(T_dim) * 1.0).tolist()
args_dict['T'] = T
call_and_print(method_name, args_dict)
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

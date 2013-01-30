import time
import requests
import json
#
import FakeEngine as FE
from FakeEngine import FakeEngine


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


# an explicit example of a method call
method_name = 'initialize'
args_dict = {"M_c":"M_c", "M_r":"M_r", "T":"T", "i":"i"}
call_and_print(method_name, args_dict)
time.sleep(1)

# programmatically call all the other method calls
method_name_to_args = FE.get_method_name_to_args()
for method_name, arg_str_list in method_name_to_args.iteritems():
    args_dict = dict(zip(arg_str_list, arg_str_list))
    call_and_print(method_name, args_dict)
    time.sleep(1)

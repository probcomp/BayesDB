import time
import requests
import json

URI = 'http://localhost:8007'

id = 0

def create_message(method_str, params):
    global id
    id += 1
    message = {
        'jsonrpc': '2.0',
        'method': method_str,
        'params': params,
        'id': str(id),
        }
    return json.dumps(message)

# an explicit example of a method call
method_name = 'initialize'
args_dict = {"M_c":"M_c", "M_r":"M_r", "T":"T", "i":"i"}
message = create_message(method_name, args_dict)
print 'trying message:', message
r = requests.put(URI, data=message)
r.raise_for_status()
print json.loads(r.content)
print
time.sleep(1)

import FakeEngine as FE
from FakeEngine import FakeEngine

# programmatically call all the other method calls
method_name_to_args = FE.get_method_name_to_args()
for method_name, arg_str_list in method_name_to_args.iteritems():
    args_dict = dict(zip(arg_str_list, arg_str_list))
    message = create_message(method_name, args_dict)
    print 'trying message:' , message
    r = requests.put(URI, data=message)
    r.raise_for_status()
    print json.loads(r.content)
    print
    time.sleep(1)

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

print
message = create_message('impute', {"M_c":"M_c", "X_L":"X_L", "X_D":"X_D", "Y":"Y", "q":"q", "n":"n"})
print 'trying message:', message
r = requests.put(URI, data=message)
r.raise_for_status()
print json.loads(r.content)
print

time.sleep(1)

print
message = create_message('initialize', {"M_c":"M_c", "M_r":"M_r", "T":"T", "i":"i"})
print 'trying message:', message
r = requests.put(URI, data=message)
r.raise_for_status()
print json.loads(r.content)
print

time.sleep(1)

print
message = create_message('analyze', {"S":"S", "T":"T", "X_L":"X_L", "X_D":"X_D", "M_c":"M_c", "M_r":"M_r", "kernel_list":"kernel_list", "n_steps":"n_steps", "c":"c", "r":"r", "max_iterations":"max_iterations", "max_time":"max_time"})
print 'trying message:', message
r = requests.put(URI, data=message)
r.raise_for_status()
print json.loads(r.content)
print

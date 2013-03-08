import requests
import json


# helper functions
def create_message(method_name, params, id):
    id += 1
    message = {
        'jsonrpc': '2.0',
        'method': method_name,
        'params': params,
        'id': str(id),
        }
    try:
        json_message = json.dumps(message)
    except Exception, e:
        import pdb
        pdb.set_trace()
        print e
    return json_message, id

def call(method_name, args_dict, URI, id=0, print_message=False):
    message, id = create_message(method_name, args_dict, id)
    if print_message: print 'trying message:', message
    r = requests.put(URI, data=message)
    r.raise_for_status()
    out = json.loads(r.content)
    if isinstance(out, dict) and 'result' in out:
        return out['result'], id
    else:
        print "call(): ERROR"
        return out, id

def call_and_print(method_name, args_dict, URI, id=0):
    out, id = call(method_name, args_dict, URI, id=id, print_message=True)
    print out
    print
    return out, id

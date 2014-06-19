#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Dan Lovell and Jay Baxter
#   Authors: Dan Lovell, Baxter Eaves, Jay Baxter, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
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
import requests
import json


global_id = 0

def create_message(method_name, params, id):
    id += 1
    message = {
        'jsonrpc': '2.0',
        'method': method_name,
        'params': params,
        'id': str(id),
        }
    json_message = json.dumps(message)
    return json_message, id

def call(method_name, args_dict, URI, id=None, print_message=False):
    global global_id
    if id is None: id = global_id
    message, id = create_message(method_name, args_dict, id)
    global_id = global_id + 1
    if print_message: print 'trying message:', message
    r = requests.put(URI, data=message)
    r.raise_for_status()
    out = json.loads(r.content)
    #
    if isinstance(out, dict) and 'result' in out:
        out = out['result']
    else:
        print "call(%s, <args_dict>, %s): ERROR" % (method_name, URI)
    return out, id

def call_and_print(method_name, args_dict, URI, id=0):
    out, id = call(method_name, args_dict, URI, id=id, print_message=True)
    print out
    print
    return out, id

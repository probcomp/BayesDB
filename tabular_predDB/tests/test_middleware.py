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
import os
import subprocess
import tabular_predDB.jsonrpc_http.middleware_stub_client as msc
import time

def test_middleware():
    os.system('pkill -f server_jsonrpc')
    os.system('nohup python -u ../jsonrpc_http/server_jsonrpc.py >server_jsonrpc.out 2>server_jsonrpc.err &')
    os.system('nohup python -u ../jsonrpc_http/middleware_server_jsonrpc.py >middleware_server_jsonrpc.out 2>middleware_server_jsonrpc.err &')
    time.sleep(3)
    msc.run_test()
    os.system('pkill -f server_jsonrpc')

if __name__ == '__main__':
    test_middleware()

import os
import subprocess
import tabular_predDB.jsonrpc_http.middleware_stub_client as msc
import time

def test_middleware():
    os.system('pkill -f server_jsonrpc')
    os.system('nohup python -u ../jsonrpc_http/server_jsonrpc.py >server_jsonrpc.out 2>server_jsonrpc.err &')
    os.system('nohup python -u ../jsonrpc_http/middleware_server_jsonrpc.py >middleware_server_jsonrpc.out 2>middleware_server_jsonrpc.err &')
    time.sleep(1)
    msc.run_test()
    os.system('pkill -f server_jsonrpc')

if __name__ == '__main__':
    test_middleware()

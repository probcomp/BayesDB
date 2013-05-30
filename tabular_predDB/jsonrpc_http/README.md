tabular_predDB/jsonrpc_http
==============

tabular predictive database stub server

Running tests
---------------------------
    > cd /path/to/tabular_predDB/jsonrpc_http
    > python server_jsonrpc.py >server_jsonrpc.out 2>server_jsonrpc.err &
    > python stub_client_jsonrpc.py >stub_client_jsonrpc.out 2>stub_client_jsonrpc.err
    > # terminate the server
    > pkill -f server_jsonrpc

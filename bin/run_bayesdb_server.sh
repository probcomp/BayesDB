#workon tabular_predDB
pkill -f python\.\*/bayesdb_server_jsonrpc.py
mkdir -p server_logs
nohup python -u bayesdb/jsonrpc/bayesdb_server_jsonrpc.py >server_logs/bayesdb_server_jsonrpc.out 2>server_logs/bayesdb_server_jsonrpc.err &

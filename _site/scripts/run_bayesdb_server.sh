pkill -f python\.\*/jsonrpc_server.py
mkdir -p server_logs
nohup python -u bayesdb/jsonrpc_server.py >server_logs/jsonrpc_server.out 2>server_logs/jsonrpc_server.err &

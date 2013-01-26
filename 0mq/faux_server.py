import argparse
import operator
import time
import sys
#
import jsonrpc2_zeromq
import jsonrpc2_zeromq.common

class RPCTestServer(jsonrpc2_zeromq.RPCServer):

    def handle_echo_method(self, msg):
        return msg

    def handle_initialize_method(self, X_L, X_D, M_C, M_R):
        args_as_str = ", ".join(map(str, [X_L, X_D, M_C, M_R]))
        msg = "ran: initialize(" + args_as_str + ")"
        return msg

    def handle_analyze_method(self, S, T, X_L, X_D, M_C, M_R, kernel_list,
                              n_steps, c, r, max_iterations, max_time):
        args_as_str = ", ".join(map(str, [S, T, X_L, X_D, M_C, M_R, kernel_list,
                                          n_steps, c, r, max_iterations,
                                          max_time]))
        msg = "ran: analyze(" + args_as_str + ")"
        return msg

    def handle_simplepredictivesample_method(self, X_L, X_D, Y, q):
        args_as_str = ", ".join(map(str, [X_L, X_D, Y, q]))
        msg = "ran: simplepredictivesample(" + args_as_str + ")"
        return msg


parser = argparse.ArgumentParser()
parser.add_argument('--is_client', action='store_true')
parser.add_argument('--is_server', action='store_true')
parser.add_argument('--port', type=int, default=5557)
parser.add_argument('--lifetime', type=int, default=10)
args = parser.parse_args()
is_client = args.is_client
is_server = args.is_server
port = args.port
lifetime = args.lifetime

if not operator.xor(is_client, is_server):
    print "must specify ONE of client or server"
    sys.exit()

endpoint = "tcp://127.0.0.1:%s" % port
if is_client:
    client = jsonrpc2_zeromq.RPCClient(endpoint=endpoint)
    msg = client.echo("hello")
    print msg, " = client.echo(\"hello\")"
    msg = client.simplepredictivesample("X_L", "X_D", "Y", "q")
    print msg, " = client.simplepredictivesample(\"X_L\", \"X_D\", \"Y\", \"q\")"
else:
    print "starting server"
    server = RPCTestServer(endpoint)
    server.start()
    if lifetime != -1:
        print "killing server in ", lifetime, " seconds"
        time.sleep(lifetime)
        print "killing server"
        server.stop()
        server.join()
        server.close()
        time.sleep(0.1)
        print "server killed"

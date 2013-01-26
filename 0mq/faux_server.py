import argparse
import operator
import time
import sys
#
import jsonrpc2_zeromq
import jsonrpc2_zeromq.common

class RPCTestServer(jsonrpc2_zeromq.RPCServer):

    def handle_initialize_method(self, M_c, M_r, T, i):
        X_L = {}
        X_D = [[]]
        return M_c, M_r, X_L, X_D

    def handle_analyze_method(self, S, T, X_L, X_D, M_C, M_R, kernel_list,
                              n_steps, c, r, max_iterations, max_time):
        X_L_prime = {}
        X_D_prime = [[]]
        return X_L_prime, X_D_prime

    def handle_simple_predictive_sample_method(self, M_c, X_L, X_D, Y, q):
        x = []
        return x

    def handle_simple_predictive_probability_method(self, M_c, X_L, X_D, Y, Q,
                                                    n):
        p = None
        return p

    def handle_impute_method(self, M_c, X_L, X_D, Y, q, n):
        e = []
        return e

    def handle_conditional_entropy_method(M_c, X_L, X_D, d_given, d_target,
                                   n=None, max_time=None):
        e = None
        return e

    def handle_predictively_related_method(self, M_c, X_L, X_D, d,
                                           n=None, max_time=None):
        m = []
        return m

    def handle_contextual_structural_similarity_method(self, X_D, r, d):
        s = []
        return s

    def handle_structural_similarity_method(self, X_D, r):
        s = []
        return s

    def handle_structural_anomalousness_columns_method(self, X_D):
        a = []
        return s

    def handle_structural_anomalousness_rows_method(self, X_D):
        a = []
        return s

    def handle_predictive_anomalousness_method(self, M_c, X_L, X_D, T, q, n):
        a = []
        return s

if __name__ == '__main__':
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
        args = ("M_c", "X_L", "X_D", "Y", "q")
        args_joined = ", ".join(args)
        msg = client.simple_predictive_sample(*args)
        print msg, " = client.simple_predictive_sample(" + args_joined + ")"
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

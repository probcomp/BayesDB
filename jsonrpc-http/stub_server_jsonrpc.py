from __future__ import print_function
#
#  Copyright (c) 2011 Edward Langley
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
#
#  Redistributions in binary form must reproduce the above copyright
#  notice, this list of conditions and the following disclaimer in the
#  documentation and/or other materials provided with the distribution.
#
#  Neither the name of the project's author nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#  TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#

from twisted.internet import reactor, ssl
from twisted.web import server
import traceback

from jsonrpc.server import ServerEvents, JSON_RPC

class ExampleServer(ServerEvents):
	# inherited hooks
	def log(self, responses, txrequest, error):
		print(txrequest.code, end=' ')
		if isinstance(responses, list):
			for response in responses:
				msg = self._get_msg(response)
				print(txrequest, msg)
		else:
			msg = self._get_msg(responses)
			print(txrequest, msg)

	def findmethod(self, method, args=None, kwargs=None):
		if method in self.methods:
			return getattr(self, method)
		else:
			return None

	# helper methods
	methods = set(['initialize', 'analyze', 'simple_predictive_sample', 'simple_predictive_probability', 'impute', 'conditional_entropy', 'predictively_related', 'contextual_structural_similarity', 'structural_similarity', 'structural_anomalousness_columns', 'structural_anomalousness_rows', 'predictive_anomalousness'])
	def _get_msg(self, response):
		print('response', repr(response))
		return ' '.join(str(x) for x in [response.id, response.result or response.error])

        def initialize(self, M_c, M_r, T, i):
            X_L = {}
            X_D = [[]]
            return M_c, M_r, X_L, X_D

        def analyze(self, S, T, X_L, X_D, M_c, M_r, kernel_list,
                    n_steps, c, r, max_iterations, max_time):
            X_L_prime = {}
            X_D_prime = [[]]
            return X_L_prime, X_D_prime

        def simple_predictive_sample(self, M_c, X_L, X_D, Y, q):
            x = []
            return x

        def simple_predictive_probability(self, M_c, X_L, X_D, Y, Q,
                                          n):
            p = None
            return p

        def impute(self, M_c, X_L, X_D, Y, q, n):
            e = []
            return e

        def conditional_entropy(M_c, X_L, X_D, d_given, d_target,
                                n=None, max_time=None):
            e = None
            return e
        
        def predictively_related(self, M_c, X_L, X_D, d,
                                 n=None, max_time=None):
            m = []
            return m
        
        def contextual_structural_similarity(self, X_D, r, d):
            s = []
            return s
        
        def structural_similarity(self, X_D, r):
            s = []
            return s
        
        def structural_anomalousness_columns(self, X_D):
            a = []
            return a
        
        def structural_anomalousness_rows(self, X_D):
            a = []
            return a
        
        def predictive_anomalousness(self, M_c, X_L, X_D, T, q, n):
            a = []
            return a

root = JSON_RPC().customize(ExampleServer)
site = server.Site(root)


# 8007 is the port you want to run under. Choose something >1024
PORT = 8007
print('Listening on port %d...' % PORT)
reactor.listenTCP(PORT, site)
reactor.run()

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

import FakeEngine as FE
from FakeEngine import FakeEngine

from FakeEngine import FakeEngine
fake_engine = FakeEngine()
FakeEngine_methods = FE.get_method_names()

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
			return getattr(fake_engine, method)
		else:
			return None

	# helper methods
	methods = set(FakeEngine_methods)
	def _get_msg(self, response):
		print('response', repr(response))
		return ' '.join(str(x) for x in [response.id, response.result or response.error])


root = JSON_RPC().customize(ExampleServer)
site = server.Site(root)


# 8007 is the port you want to run under. Choose something >1024
PORT = 8007
print('Listening on port %d...' % PORT)
reactor.listenTCP(PORT, site)
reactor.run()

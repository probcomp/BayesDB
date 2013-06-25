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

from twisted.internet import ssl
import traceback
from twisted.internet import reactor
from twisted.web import server
from jsonrpc.server import ServerEvents, JSON_RPC
#
import tabular_predDB.LocalEngine as LE
import tabular_predDB.python_utils.general_utils as gu


class ExampleServer(ServerEvents):

	get_next_seed = gu.int_generator(start=0)
	methods = set(gu.get_method_names(LE.LocalEngine))

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
			next_seed = self.get_next_seed.next()
			engine = LE.LocalEngine(next_seed)
			return getattr(engine, method)
		else:
			return None

	# helper methods
	def _get_msg(self, response):
		ret_str = str(response)
		if hasattr(response, 'id'):
			ret_str = str(response.id)
			if response.result:
				ret_str += '; result: %s' % str(response.result)
			else:
				ret_str += '; error: %s' % str(response.error)
		return ret_str

root = JSON_RPC().customize(ExampleServer)
site = server.Site(root)


# 8007 is the port you want to run under. Choose something >1024
PORT = 8007
print('Listening on port %d...' % PORT)
reactor.listenTCP(PORT, site)
reactor.run()

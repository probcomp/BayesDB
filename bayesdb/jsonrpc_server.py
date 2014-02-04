#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
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
from twisted.web import server, iweb
from twisted.web.resource import EncodingResourceWrapper

from jsonrpc.server import ServerEvents, JSON_RPC

import bayesdb.engine as engine_module
engine_methods = engine_module.get_method_names()
from bayesdb.engine import Engine
engine = Engine()

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
                  return getattr(engine, method)
            else:
                  return None
            
      # helper methods
      methods = set(engine_methods)
      def _get_msg(self, response):
            ret_str = 'No id response: %s' % str(response)
            if hasattr(response, 'id'):
                  ret_str = str(response.id)
                  if response.result:
                        ret_str += '; result: %s' % str(response.result)
                  else:
                        ret_str += '; error: %s' % str(response.error)
                        for at in dir(response):
                              if not at.startswith('__'):
                                    print(at + ": " + str(getattr(response, at)))
                        print("response:\n" + str(dir(response)))
            return ret_str
      
      
class CorsEncoderFactory(object):
      def encoderForRequest(self, request):
            request.setHeader("Access-Control-Allow-Origin", '*')
            request.setHeader("Access-Control-Allow-Methods", 'PUT, GET')
            return _CorsEncoder(request)

class _CorsEncoder(object):
      """
      @ivar _request: A reference to the originating request.
      
      @since: 12.3
      """
      
      def __init__(self, request):
            self._request = request
            
      def encode(self, data):
            return data
      
      def finish(self):
            return ""


root = JSON_RPC().customize(ExampleServer)
wrapped = EncodingResourceWrapper(root, [CorsEncoderFactory()])
site = server.Site(wrapped)

# 8008 is the port you want to run under. Choose something >1024
PORT = 8008
print('Listening on port %d...' % PORT)
reactor.listenTCP(PORT, site)
reactor.run()

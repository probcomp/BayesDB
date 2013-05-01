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
import subprocess
import os

def test_component_model():
    run_shell_command('test_component_model')

def test_continuous_component_model():
    run_shell_command('test_continuous_component_model')

def test_multinomial_component_model():
    run_shell_command('test_multinomial_component_model')

def test_cluster():
    run_shell_command('test_cluster')

def run_shell_command(name):
    p = subprocess.Popen(['%s/%s' % (os.path.dirname(os.path.abspath(__file__)), name)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    retcode = p.wait()
    out = p.stdout.read()
    err = p.stderr.read()
    if len(err) > 0:
        fail(err)


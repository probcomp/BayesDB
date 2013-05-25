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
#!python
import os


class path():
    user_home_dir = os.environ['HOME']
    if 'WORKSPACE' in os.environ:
        user_home_dir = os.environ['WORKSPACE']
    remote_code_dir = os.path.join('/home/sgeadmin', 'tabular_predDB')
    this_dir = os.path.dirname(os.path.abspath(__file__))
    this_repo_dir = os.path.abspath(os.path.join(this_dir, '..'))
    install_script_dir = os.path.join(remote_code_dir, 'install_scripts')
    web_resources_dir = os.path.join(remote_code_dir, 'www')
    web_resources_data_dir = os.path.join(web_resources_dir, 'data')
    #
    install_ubuntu_script = os.path.join(install_script_dir,
                                         'install_ubuntu_packages.sh')
    install_boost_script = os.path.join(install_script_dir, 'install_boost.sh')
    postgres_setup_script = os.path.join(install_script_dir, 'postgres_setup.sh')
    virtualenv_setup_script = os.path.join(install_script_dir,
                                           'virtualenv_setup.sh')
    run_server_script = os.path.join(remote_code_dir, 'run_server.sh')
    run_webserver_script = os.path.join(remote_code_dir, 
                                        'run_simplehttpserver.sh')
    # server_script = os.path.join('jsonrpc_http', 'server_jsonrpc.py')
    try:
        os.makedirs(web_resources_dir)
        os.makedirs(web_resources_data_dir)
    except Exception, e:
        pass

class s3():
    bucket_str = 'mitpcp-tabular-predDB'
    bucket_dir = ''
    ec2_credentials_file = os.path.expanduser('~/.boto')

class gdocs():
    auth_file = os.path.expanduser("~/mh_gdocs_auth")
    gdocs_folder_default = "MH"

class git():
    # repo_prefix = 'https://github.com/'
    # repo_prefix = 'git://github.com/'
    repo_prefix = 'git@github.com:'
    repo_suffix = 'mit-probabilistic-computing-project/tabular-predDB.git'
    repo = repo_prefix + repo_suffix
    branch = 'sdl_client_work'

#!python
#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Dan Lovell and Jay Baxter
#   Authors: Dan Lovell, Baxter Eaves, Jay Baxter, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
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
import os
#
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log


project_name = 'bayesdb'
#
repo_url = 'https://github.com/mit-probabilistic-computing-project/%s.git' % project_name
get_repo_dir = lambda user: os.path.join('/home', user, project_name)
get_setup_script = lambda user: os.path.join(get_repo_dir(user), 'setup.py')


class bayesdbSetup(ClusterSetup):

    def __init__(self):
        # TODO: Could be generalized to "install a python package plugin"
        pass

    def run(self, nodes, master, user, user_shell, volumes):
        # set up some paths
        repo_dir = get_repo_dir(user)
        setup_script = get_setup_script(user)
        for node in nodes:
            # NOTE: nodes includes master
            log.info("Installing %s as root on %s" % (project_name, node.alias))
            #
            cmd_strs = [
                # FIXME: do this somewhere else
                'pip install pyparsing==2.0.1',
                'pip install patsy',
                'pip install statsmodels',
                'rm -rf %s' % repo_dir,
                'git clone %s %s' % (repo_url, repo_dir),
                'python %s develop' % setup_script,
                # 'python %s build_ext --inplace' % setup_script,
                'chown -R %s %s' % (user, repo_dir),
            ]
            for cmd_str in cmd_strs:
                node.ssh.execute(cmd_str + ' >out 2>err')
                pass
            pass
        for node in nodes:
            log.info("Setting up %s as %s on %s" % (project_name, user, node.alias))
            #
            cmd_strs = [
                'mkdir -p ~/.matplotlib',
                'echo backend: Agg > ~/.matplotlib/matplotlibrc',
            ]
            for cmd_str in cmd_strs:
                node.shell(user=user, command=cmd_str)
                pass
            pass
        return

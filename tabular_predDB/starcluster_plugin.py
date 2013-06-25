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
import tempfile
#
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
#
import tabular_predDB.settings as S

# maybe should prefix the command with "source /etc/profile"
# as starclusters' sshutils.ssh.execute(..., source_profile=True) does
def run_as_user(node, user, command_str, **kwargs):
     cmd_str = 'sudo -H -u %s %s'
     cmd_str %= (user, command_str)
     node.ssh.execute(cmd_str, **kwargs)

def auto_accept_key(node, user):
     # make sure you can programmatically ssh into node
     cmd_str = 'ssh -i %s -o StrictHostKeyChecking=no %s@%s echo $(hostname)'
     cmd_str %= (node.key_location, user, node.ip_address)
     os.system(cmd_str)

def create_pushable_remote_repo(remote_code_dir, node):
     # make sure you remove the old code
     cmd_str = 'rm -rf %s'
     cmd_str %= remote_code_dir
     node.ssh.execute(cmd_str)
     # prepare remote for push
     cmd_str = ' && '.join([
               'mkdir -p %s',
               'cd %s',
               'git init',
               'git config --add receive.denyCurrentBranch ignore'
               ])
     cmd_str %= (remote_code_dir, remote_code_dir)
     node.ssh.execute(cmd_str)

def push_repo_using_node_key(remote_code_dir, node,
                             git_ssh_file='/tmp/git_ssh.sh'):
     # make GIT_SSH script
     cmd_str = 'echo \'ssh -i %s $1 $2\' > %s && chmod a+x %s'
     cmd_str %= (node.key_location, git_ssh_file, git_ssh_file)
     os.system(cmd_str)
     # push up from LOCAL to remote
     cmd_str = 'export GIT_SSH=%s && git push ssh://root@%s%s/ master'
     cmd_str %= (git_ssh_file, node.ip_address, remote_code_dir)
     os.system(cmd_str)

def update_remote_repo_working_tree(remote_code_dir, node, user):
     # update remote working tree
     cmd_str = 'cd %s && git reset --hard'
     cmd_str %= remote_code_dir
     node.ssh.execute(cmd_str)
     # set remote origin to tabular_predDB github
     cmd_str = 'bash -c "cd %s && git remote set-url origin https://github.com/%s"'
     cmd_str %= (remote_code_dir, S.git.repo_suffix)
     run_as_user(node, user, cmd_str)
     #
     cmd_str = 'chown -R sgeadmin:sgeadmin %s'
     cmd_str %= remote_code_dir
     node.ssh.execute(cmd_str)
     # FIXME: Where is the update?

# this complains about 
# fatal: Not a git repository (or any of the parent directories): .git
def push_local_repo_to_new_remote(remote_code_dir, node, user):
     auto_accept_key(node, user)
     create_pushable_remote_repo(remote_code_dir, node)
     push_repo_using_node_key(remote_code_dir, node)
     update_remote_repot_working_tree(remote_code_dir, node)

def copy_this_repo(remote_code_dir, node, user, branch='master',
                   temp_base_dir='/tmp/'):
     local_dir = os.path.join(os.path.split(__file__)[0], '..')
     # generate temporary resources
     temp_dir_name = tempfile.mkdtemp(dir=temp_base_dir)
     temp_tgz_name = tempfile.mktemp(dir=temp_base_dir)
     # clone into temp dir
     cmd_str = 'git clone %s %s'
     cmd_str %= (local_dir, temp_dir_name)
     os.system(cmd_str)
     # tgz for speed
     cmd_str = 'cd %s && tar cvfz %s . >tar.out 2>tar.err'
     cmd_str %= (temp_dir_name, temp_tgz_name)
     os.system(cmd_str)
     # put up to node and untar
     node.ssh.put(temp_tgz_name, temp_tgz_name)
     cmd_str = ' && '.join([
               'mkdir -p %s',
               'cd %s',
               'tar xvfz %s',
               'git checkout %s',
               'chown -R %s .'
               ])
     cmd_str %= (remote_code_dir, remote_code_dir, temp_tgz_name,
                 branch, user)
     node.ssh.execute(cmd_str)
     # clean up
     cmd_str = 'rm -rf %s %s'
     cmd_str %= (temp_tgz_name, temp_dir_name)
     os.system(cmd_str)
     update_remote_repo_working_tree(remote_code_dir, node, user)

class tabular_predDBSetup(ClusterSetup):
     def __init__(self):
         # TODO: Could be generalized to "install a python package plugin"
         pass

     def run(self, nodes, master, user, user_shell, volumes):
          # NOTE: nodes includes master
          remote_home_dir = os.path.join('/home/', user)
          for node in nodes:
               log.info("Installing tabular_predDB (part 1) on %s"
                        % node.alias)
               # push code up
               copy_this_repo(S.path.remote_code_dir, node, user,
                              S.git.branch)
          for node in nodes:
               log.info("Installing tabular_predDB (part 2) on %s"
                        % node.alias)
               # install ubuntu packages
               log.info("Installing ubuntu packages on %s" % node.alias)
               # apt-get update
               cmd_str = 'apt-get update'
               node.ssh.execute(cmd_str)
               # install ubuntu packages
               cmd_str = 'bash %s >ubuntu.out 2>ubuntu.err'
               cmd_str %= S.path.install_ubuntu_script.replace(S.path.this_repo_dir, S.path.remote_code_dir)
               node.ssh.execute(cmd_str)
               # install boost
               log.info("Installing boost on %s" % node.alias)
               cmd_str = 'bash %s >boost.out 2>boost.err'
               cmd_str %= S.path.install_boost_script.replace(S.path.this_repo_dir, S.path.remote_code_dir)
               node.ssh.execute(cmd_str)
               # install python packages in a virtual env
               log.info("Installing python packages on %s" % node.alias)
               cmd_str = 'bash -i %s %s >virtualenv.out 2>virtualenv.err'
               cmd_str %= (S.path.virtualenv_setup_script.replace(S.path.this_repo_dir, S.path.remote_code_dir), user)
               node.ssh.execute(cmd_str)
               # make sure agg backend is used
               cmd_str = ' && '.join([
                         'mkdir -p %s/.matplotlib',
                         'echo backend: Agg > %s/.matplotlib/matplotlibrc',
                         'chown -R %s:%s %s/.matplotlib',
                         ])
               cmd_str %= (remote_home_dir,
                           remote_home_dir,
                           user, user, remote_home_dir)
               node.ssh.execute(cmd_str)
               # compile cython
               log.info("Installing engine (compiling cython) on %s" % node.alias)
               cmd_str = 'bash -c -i "workon tabular_predDB && make cython"'
               run_as_user(node, user, cmd_str)
               # set up postgres user, database
               postgres_setup_script = S.path.postgres_setup_script.replace(S.path.this_repo_dir, S.path.remote_code_dir)
               postgres_setup_script_path = os.path.split(postgres_setup_script)[0]
               cmd_str = 'cd %s && bash %s'
               cmd_str %= (postgres_setup_script_path, postgres_setup_script)
               node.ssh.execute(cmd_str)
               # run server
               cmd_str = 'bash -i %s'
               cmd_str %= S.path.run_server_script.replace(S.path.this_repo_dir, S.path.remote_code_dir)
               run_as_user(node, user, cmd_str)
               #
               cmd_str = "bash -i %s %s" % (S.path.run_webserver_script.replace(S.path.this_repo_dir, S.path.remote_code_dir),
                                            S.path.web_resources_dir.replace(S.path.this_repo_dir, S.path.remote_code_dir))
               run_as_user(node, user, cmd_str)

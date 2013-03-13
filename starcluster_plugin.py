#!python
import os
import tempfile
#
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
#
import tabular_predDB.settings as S

run_as_user = lambda node, user, command_str: \
    node.ssh.execute('sudo -u %s %s' % (user, command_str))

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

def update_remote_repo_working_tree(remote_code_dir, node):
     # update remote working tree
     cmd_str = 'cd %s && git reset --hard'
     cmd_str %= remote_code_dir
     node.ssh.execute(cmd_str)
     # chown
     cmd_str = 'chown -R %s %s'
     cmd_str %= (user, remote_code_dir)
     node.ssh.execute(cmd_str)

# this complains about 
# fatal: Not a git repository (or any of the parent directories): .git
def push_local_repo_to_new_remote(remote_code_dir, node, user):
     auto_accept_key(node, user)
     create_pushable_remote_repo(remote_code_dir, node)
     push_repo_using_node_key(remote_code_dir, node)
     update_remote_repot_working_tree(remote_code_dir, node)

def copy_this_repo(remote_code_dir, node, user, branch=None,
                   temp_base_dir='/tmp/'):
     local_dir = os.path.split(__file__)[0]
     # generate temporary resources
     temp_dir_name = tempfile.mkdtemp(dir=temp_base_dir)
     temp_tgz_name = tempfile.mktemp(dir=temp_base_dir)
     # clone into temp dir
     cmd_str = 'git clone %s %s'
     cmd_str %= (local_dir, temp_dir_name)
     os.system(cmd_str)
     # tgz for speed
     cmd_str = 'cd %s && tar cvfz %s .'
     cmd_str %= (temp_dir_name, temp_tgz_name)
     os.system(cmd_str)
     # put up to node and untar
     node.ssh.put(temp_tgz_name, temp_tgz_name)
     cmd_str = 'mkdir -p %s && cd %s && tar xvfz %s && chown -R %s .'
     cmd_str %= (remote_code_dir, remote_code_dir, temp_tgz_name, user)
     node.ssh.execute(cmd_str)
     # clean up
     cmd_str = 'rm -rf %s %s'
     cmd_str %= (temp_tgz_name, temp_dir_name)
     os.system(cmd_str)
     # switch to branch
     if branch is not None:
          cmd_str = 'cd %s && git checkout %s'
          cmd_str %= (remote_code_dir, branch)
          node.ssh.execute(cmd_str)

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
               cmd_str = 'bash %s >ubuntu.out 2>ubuntu.err'
               cmd_str %= S.path.install_ubuntu_script
               node.ssh.execute(cmd_str)
               # install boost
               cmd_str = 'bash %s >boost.out 2>boost.err'
               cmd_str %= S.path.install_boost_script
               node.ssh.execute(cmd_str)
               # install python packages in a virtual env
               cmd_str = 'bash -i %s %s >virtualenv.out 2>virtualenv.err'
               cmd_str %= (S.path.virtualenv_setup_script, user)
               node.ssh.execute(cmd_str)
               # make sure agg backend is used
               cmd_str = ' && '.join([
                         'mkdir -p %s/.matplotlib',
                         'echo backend: Agg > %s/.matplotlib/matplotlibrc',
                         ])
               cmd_str %= (remote_home_dir, remote_home_dir)
               node.ssh.execute(cmd_str)

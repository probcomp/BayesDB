#!python
import os
#
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
#
import tabular_predDB.settings as S

run_as_user = lambda node, user, command_str: \
    node.ssh.execute('sudo -u %s %s' % (user, command_str))

class tabular_predDBSetup(ClusterSetup):
     def __init__(self):
         # TODO: Could be generalized to "install a python package plugin"
         pass

     def run(self, nodes, master, user, user_shell, volumes):
          # NOTE: nodes includes master
          boto_full_file = os.path.join(S.path.remote_home_dir, '.boto')
          clone_tuple = (S.git.repo, S.path.remote_code_dir)
          checkout_tuple = (S.path.remote_code_dir, S.git.branch)
          local_ssh_key = os.path.expanduser('~/.ssh/id_rsa')
          remote_ssh_key_dir = os.path.join(S.path.remote_home_dir, '.ssh')
          #
          for node in nodes:
               log.info("Copying up boto file on %s" % node.alias)
               node.ssh.put(S.s3.ec2_credentials_file, S.path.remote_home_dir)
               node.ssh.execute('chmod -R ugo+rwx %s' % boto_full_file)
               node.ssh.put(local_ssh_key, remote_ssh_key_dir)
               node.ssh.put(local_ssh_key + '.pub', remote_ssh_key_dir)
               node.ssh.put(local_ssh_key, '/root/.ssh/')
               node.ssh.put(local_ssh_key + '.pub', '/root/.ssh/')
          for node in nodes:
               log.info("Installing tabular_predDB (part 1) on %s" % node.alias)
               #
               node.ssh.execute('rm -rf %s' % clone_tuple[-1])
               node.ssh.execute('ssh -o StrictHostKeyChecking=no git@github.com', ignore_exit_status=True)
               node.ssh.execute('git clone %s %s' % clone_tuple)
               node.ssh.execute('cd %s && git checkout %s' % checkout_tuple)
               node.ssh.execute('chmod -R ugo+rwx %s' % clone_tuple[-1])
               node.ssh.execute('chown -R sgeadmin %s' % clone_tuple[-1])
          for node in nodes:
               log.info("Installing tabular_predDB (part 2) on %s" % node.alias)
               node.ssh.execute('pip install virtualenv')
               node.ssh.execute('pip install virtualenvwrapper')
               # install ubuntu packages
               command_str = 'bash %s' % S.path.install_ubuntu_script
               node.ssh.execute(command_str)
               # install boost
               command_str = 'bash %s >out2 2>err2' % S.path.install_boost_script
               node.ssh.execute(command_str)
               #
               command_str = 'bash -i %s %s >out1 2>err1' % (S.path.virtualenv_setup_script, 'sgeadmin')
               node.ssh.execute(command_str)

#!python
import os
#
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
#
import tabular_predDB.settings as S


class tabular_predDBSetup(ClusterSetup):
     def __init__(self):
         # TODO: Could be generalized to "install a python package plugin"
         pass

     def run(self, nodes, master, user, user_shell, volumes):
          # NOTE: nodes includes master
          boto_full_file = os.path.join(S.path.remote_home_dir, '.boto')
          clone_tuple = (S.git.repo, S.path.remote_code_dir)
          checkout_tuple = (S.path.remote_code_dir, S.git.branch)
          #
          for node in nodes:
               log.info("Copying up boto file on %s" % node.alias)
               node.ssh.put(S.s3.ec2_credentials_file, S.path.remote_home_dir)
               node.ssh.execute('chmod -R ugo+rwx %s' % boto_full_file)
               node.ssh.put(os.path.expanduser('~/.ssh/id_rsa'), os.path.join(S.path.remote_home_dir, '.ssh'))
          for node in nodes:
               log.info("Installing tabular_predDB (part 1) on %s" % node.alias)
               #
               # node.ssh.execute('rm -rf %s' % clone_tuple[-1])
               # node.ssh.execute('git clone %s %s' % clone_tuple)
               node.ssh.execute('cd %s && git checkout %s' % checkout_tuple)
               node.ssh.execute('chmod -R ugo+rwx %s' % clone_tuple[-1])
          for node in nodes:
               log.info("Installing tabular_predDB (part 2) on %s" % node.alias)
               node.ssh.execute('apt-get install -y libfreetype6-dev')
               node.ssh.execute('apt-get install -y libpng12-dev')
               node.ssh.execute('cd %s && bash -i %s' %
                                (S.path.remote_code_dir,
                                 S.path.install_boost_script))
               node.ssh.execute('cd %s && bash -i %s' %
                                (S.path.remote_code_dir,
                                 S.path.virtualenv_setup_script))

#!python
import os


class path():
    remote_home_dir = '/home/sgeadmin/'
    remote_code_dir = '/home/sgeadmin/tabular_predDB'
    install_boost_script = os.path.join(remote_code_dir, 'install_boost.sh')
    virtualenv_setup_script = os.path.join(remote_code_dir, 'virtualenv_setup.sh')

class s3():
    bucket_str = 'mitpcp-tabular-predDB'
    bucket_dir = ''
    ec2_credentials_file = os.path.expanduser('~/.boto')

class gdocs():
    auth_file = os.path.expanduser("~/mh_gdocs_auth")
    gdocs_folder_default = "MH"

class git():
    repo_prefix = 'https://github.com/'
    repo_suffix = 'mit-probabilistic-computing-project/tabular-predDB.git'
    repo = os.path.join(repo_prefix, repo_suffix)
    branch = 'multinomial-integration'

#!python
import os


class path():
    remote_code_dir = '/home/sgeadmin/tabular_predDB'
    install_ubuntu_script = os.path.join(remote_code_dir,
                                         'install_ubuntu_packages.sh')
    install_boost_script = os.path.join(remote_code_dir, 'install_boost.sh')
    virtualenv_setup_script = os.path.join(remote_code_dir,
                                           'virtualenv_setup.sh')
    server_script = os.path.join('jsonrpc_http', 'server_jsonrpc.py')
    run_server_script = 'run_server.sh'
    run_webserver_script = os.path.join(remote_code_dir, 
                                        'run_simplehttpserver.sh')
    postgres_setup_script = 'postgres_setup.sh'
    web_resources_dir = os.path.join(remote_code_dir, 'web_resources')
    web_resources_data_dir = os.path.join(remote_code_dir, 'web_resources', 'data')
    try:
        os.makedirs(web_resources_dir)
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
    branch = 'master'

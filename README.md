tabular-predDB
==============

tabular predictive database

This package is configured to be installed as a StarCluster plugin.  Roughly, the following are prerequisites.
* An EC2 account
    * EC2 credentials in a ~/.boto file
* StarCluster installed on your local machine
    * ~/.starcluster/config file contains the information in /path/to/tabular_predDB/starcluster.config
* SSH access to the github repo
    * via ssh key pair, ~/.ssh/id_rsa{,.pub} that will be copied up to EC2

Everything will be set up for a user named 'sgeadmin'.  Required python packages will be installed in a virtualenv named tabular_predDB.  To access the environment necessary to build the software, the user should run
    > workon tabular_predDB
from the sgeadmin user's account

A starcluster_plugin.py file in included in this repo.  
Running server
---------------------------
    > workon tabular_predDB
    > cd /path/to/tabular-predDB
    > make cython
    > cd /path/to/tabular-predDB/jsonrpc_http
    > # capture stdout, stderr separately
    > python server_jsonrpc.py >server_jsonrpc.out 2>server_jsonrpc.err &
    > # test with 'python stub_client_jsonrpc.py'

Running tests
---------------------------
    > workon tabular_predDB
    > cd /path/to/tabular-predDB
    > # capture stdout, stderr separately
    > make runtests >tests.out 2>tests.err

Building local binary
-------------------------------------------------
    > workon tabular_predDB
    > cd /path/to/tabular-predDB
    > make bin


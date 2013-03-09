tabular-predDB
==============

tabular predictive database

This package is configured to be installed as a StarCluster plugin.  Roughly, the following are prerequisites.

* An [Amazon EC2](http://aws.amazon.com/ec2/) account
    * EC2 credentials in a [~/.boto file](https://code.google.com/p/boto/wiki/BotoConfig#Example)  **this will be copied up to EC2**
    * EC2 key pair
* [StarCluster](http://star.mit.edu/cluster/) installed on your local machine
    * ~/.starcluster/config file contains the information in [/path/to/tabular_predDB/starcluster.config](https://github.com/mit-probabilistic-computing-project/tabular-predDB/blob/master/starcluster.config) with information filled in
* [SSH access](https://help.github.com/articles/generating-ssh-keys) to the [tabular-predDB github repo](https://github.com/mit-probabilistic-computing-project/tabular-predDB) via ssh key pair, ~/.ssh/id_rsa{,.pub} **these will be copied up to EC2**
    * [[FIXME: consider 'starcluster put'ing from local to remotes]]

Everything will be set up for a user named 'sgeadmin'.  Required python packages will be installed in a virtualenv named tabular_predDB.  To access the environment necessary to build the software, you should be logged in as sgeadmin and run

    > workon tabular_predDB

A starcluster_plugin.py file in included in this repo.  Assuming the above prerequisites are fulfilled,

    > starcluster start -c tabular_predDB [cluster_name]

should start a single c1.medium StarCluster server on EC2, install the necessary software and be ready for running the engine.

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


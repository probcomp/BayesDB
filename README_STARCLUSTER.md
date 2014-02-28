BayesDB on StarCluster
======================

This package is configured to be installed as a StarCluster plugin.  Roughly, the following are prerequisites.

* An [Amazon EC2](http://aws.amazon.com/ec2/) account
    * [EC2 key pair](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/generating-a-keypair.html)
* [StarCluster](http://star.mit.edu/cluster/) installed on your local machine
    * ~/.starcluster/config file includes this repo's [starcluster.config](https://github.com/mit-probabilistic-computing-project/bayesdb/blob/master/starcluster.config) by including the following line in the [global] section

     INCLUDE=/path/to/bayesdb/starcluster.config
* You are able to start a 'smallcluster' cluster as defined in the default StarCluster config file
    * Make sure to fill in your credentials **and** have a properly defined keypair

     AWS_ACCESS_KEY_ID = #your_aws_access_key_id
     
     AWS_SECRET_ACCESS_KEY = #your_secret_access_key
     
     AWS_USER_ID= #your userid
     
     KEYNAME = mykey

    * To generate the default StarCluster config file, run

     starcluster -c [NONEXISTANT_FILE] help

A starcluster_plugin.py file in included in this repo.  Assuming the above prerequisites are fulfilled,

    local> starcluster start -s 1 -c bayesdb [CLUSTER_NAME]

should start a single c1.medium StarCluster server on EC2, install the necessary software and compile the engine.

Everything will be set up for a user named 'bayesdb'.  Required python packages will be installed to the system python.

## [Creating an AMI](http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/ApiReference-cmd-CreateImage.html) from booted instance

* Determine the instance id of the instance you want to create an AMI from.
   * You can list all instances with
    
    starcluster listinstances
    
* make sure you have your private key and X.509 certificate
   * your private key file, PRIVATE_KEY_FILE below, usually looks like pk-\<NUMBERS\_AND\_LETTERS\>.pem
   * your X.509 certificate file, CERT_FILE below, usually looks like cert-\<NUMBERS\_AND\_LETTERS\>.pem

Note, this will temporarily shut down the instance

    local> nohup ec2cim <instance-id> [--name <NAME>] [-d <DESCRIPTION>] -K ~/.ssh/<PRIVATE_KEY_FILE> -C ~/.ssh/<CERT_FILE> >out 2> err


This will start the process of creating the AMI.  It will print 'IMAGE [AMI-NAME]' to the file 'out'.  Record AMI-NAME and modify ~/.starcluster/config to use that for the bayesdb cluster's NODE\_IMAGE\_ID.

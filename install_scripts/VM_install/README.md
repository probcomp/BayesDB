VM setup
========

There are three steps to VM setup.

1. In the `host` OS, we'll install the VM
1. In the `guest` OS, we'll install tabular\_predDB.
1. In the `guest` OS, we'll run tests to verify functionality

Afterwards, you can install Jenkins to the VM if desired by following the steps in Installing Jenkins in this README

Installing the VM
==================

We'll assume you have

* Access to the tabular\_predDB repo and shell variable $REPO pointing to it
* VMware Player installed
* VMware VIX API installed
* The zipped VM image downloaded and shell variable $ZIPPED\_VM pointing to it

You'll probably want to set $REPO like this

    REPO=https://github.com/mit-probabilistic-computing-project/tabular-predDB.git

Executing the following commands will create the VM files in your home directory, spin it up, and set $VM\_IP

    # from the `host` OS
    cd
    git clone $REPO tabular_predDB
    create_vm_script=tabular_predDB/install_scripts/VM_install/create_vm.sh
    bash $create_vm_script -z $ZIPPED_VM
    VM_IP=$(bash $create_vm_script -a)

You can now ssh into the `guest` OS with

    ssh bigdata@$VM_IP

Installing tabular\_predDB
==========================

To install tabular\_predDB we have bash scripts rather than the starcluster\_plugin.py script

    # from the `guest` OS
    cd
    git clone $REPO tabular_predDB
    cd tabular_predDB/install_scripts/VM_install
    sudo bash install_to_vm_root.sh
    bash install_to_vm_user.sh

Verifying functionality
=======================

To test the install, we'll run tabular\_predDB/tests/test\_middleware.py which tests the C++ engine, the Cython wrapping and the Database layer.

    # from the `guest` OS
    export PYTHONPATH=~/tabular_predDB/:$PYTHONPATH
    cd ~/tabular_predDB/
    make tests
    make cython
    cd tabular_predDB/tests
    python test_middleware.py

Installing Jenkins
==================

Assuming you have

1. tabular_predDB installed to ~/
2. Your desired Jenkins job configuration in config.xml with shell variable $jenkins_config pointing to it 

You can install jenkins with the following commands

    # from the `guest` OS
    cd ~/tabular_predDB/install_scripts/
    sudo bash setup_jenkins.sh -u bigdata
    python create_jenkins_job_from_config.py --config_filename $jenkins_config
    bash VM_install/setup_jenkins_modifications.sh

Note: for the build step 'Execute Shell', the command should be: zsh -i jenkins_script.sh

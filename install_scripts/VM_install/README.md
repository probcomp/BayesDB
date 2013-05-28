VM setup
========

There are three steps to VM setup.

1. In the `host` OS, we'll install the VM
1. In the `guest` OS, we'll install the tabular\_predDB software.
1. In the `guest` OS, we'll run tests to verify functionality

Installing the VM
==================

We'll assume you have

* Access to the tabular\_predDB repo and shell variable $REPO pointing to it
* VMware Player installed
* VMware VIX API installed
* The zipped VM image downloaded and shell variable $ZIPPED\_VM pointing to it

Executing the following commands will create a VM in your home directory, spin it up, and set $VM\_IP

    cd
    git clone $REPO tabular_predDB
    create_vm_script=tabular_predDB/install_scripts/VM_install/create_vm.sh
    bash $create_vm_script -z $ZIPPED_VM
    VM_IP=$(bash $create_vm_script -a)

You can now ssh into the VM with

    ssh bigdata@$VM_IP

When we say "In the `guest` OS", we mean after ssh'ing into the VM

Installing tabular\_predDB into the `guest` OS
==============================================

To install tabular\_predDB in the VM, we have bash scripts rather than the starcluster\_plugin.py script

    cd
    git clone $REPO tabular_predDB
    cd tabular_predDB/install_scripts/VM_install
    sudo bash install_to_vm_root.sh
    bash install_to_vm_user.sh

To test the install, we'll run tabular\_predDB/tests/test\_middleware.py which tests the C++ engine, the Cython wrapping and the Database layer.

    export PYTHONPATH=~/tabular_predDB/:$PYTHONPATH
    cd ~/tabular_predDB/
    make tests
    make cython
    cd tabular_predDB/tabular_predDB/tests
    python test_middleware.py

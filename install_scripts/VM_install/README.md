VM setup
========

There are two steps to VM setup.

1. In the `host` OS, we'll set up the VM
1. In the `guest` OS, we'll run tests to verify functionality

Afterwards, you can install Jenkins to the VM if desired by following the steps in Installing Jenkins in this README

Setting up the VM
==================

We'll assume you have

* A local copy of the tabular\_predDB repo with shell variable $LOCAL\_REPO\_LOCATION pointing to it.
* VMware Player installed
* VMware VIX API installed
* Unzipped the VM image with shell variable $IMAGE\_LOCATION pointing to it
* Started the VM via the 'vmplayer' GUI at least once to verify VM settings are appropriate for your host OS

Executing the following commands

    # from the `host` OS
    cd $LOCAL_REPO_LOCATION/install_scripts/VM_install
    bash setup_vm.sh -i $IMAGE_LOCATION
    VM_IP=$(bash setup_vm.sh -a)

Will

1. Spin up the VM
2. Set up ssh key login for the current VM
3. Allow the bigdata user in the `guest` OS to sudo without a password
4. Install tabular-predDB requirements to the `guest` OS using /path/to/tabular\_predDB/install\_scripts/programmatic\_install.sh
5. set $VM\_IP to the VM's network address for SSH'ing in

You can now ssh into the `guest` OS with

    ssh bigdata@$VM_IP

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

FIXME: show use of jenkins_utils.py on the command line to create and invoke a job

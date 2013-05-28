Installing to a VM
==================

First, we'll install a VM to your host machine.  We'll assume you have

* Access to the tabular\_predDB repo and shell variable $REPO pointing to it
* VMware Player installed
* VMware VIX API installed
* The zipped VM image downloaded and shell variable $ZIPPED_VM pointing to it

    cd
    git clone $REPO tabular_predDB
    create_vm_script=tabular_predDB/install_scripts/VM_install/create_vm.sh
    bash $create_vm_script -z $ZIPPED_VM
    VM_IP=$(bash $create_vm_script -a)

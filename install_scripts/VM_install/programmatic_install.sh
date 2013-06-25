#!/bin/bash


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    VMware automation functions
    
    OPTIONS:
    -h      Show this message
    -i      VM=$VM
    -a      VM_IP=$VM_IP
EOF
exit
}


#Process the arguments
while getopts hi:a: opt
do
    case "$opt" in
        h) usage;;
        i) VM=$OPTARG;;
        a) VM_IP=$OPTARG;;
    esac
done


# Ensure VM was set
if [[ -z $VM ]]; then
    echo "'-i <VM>' must be passed"
    echo "not setting up VM!!!!"
    exit
fi

# Ensure VM exists
if [[ ! -f "$VM" ]]; then
    echo "VM doesn't exist: $VM"
    echo "not setting up VM !!!!"
    exit
fi

# Ensure ip_address was set
if [[ -z $VM_IP ]]; then
    echo "'-a <VM_IP>' must be passed"
    echo "not setting up VM!!!!"
    exit
fi

# BEWARE: readlink doesn't work on macs
THIS_SCRIPT_ABS_PATH=$(readlink -f "$0")
GIT_LOCATION="$(dirname $THIS_SCRIPT_ABS_PATH)/../../.git"
VM_install_path=/home/bigdata/tabular_predDB/install_scripts/VM_install/
LOCAL_TMP_DIR=$(mktemp -d)
echo "LOCAL_TMP_DIR: $LOCAL_TMP_DIR"
#
git clone --depth=1 "${GIT_LOCATION}" $LOCAL_TMP_DIR
rm -rf $LOCAL_TMP_DIR/.git
echo "about to rm -rf"
ssh bigdata@$VM_IP "sudo rm -rf ~/tabular_predDB"
scp -r $LOCAL_TMP_DIR bigdata@$VM_IP:~/tabular_predDB
ssh bigdata@$VM_IP "cd $VM_install_path && sudo bash install_to_vm_root.sh >install_to_vm_root.out 2>install_to_vm_root.err"
ssh bigdata@$VM_IP "cd $VM_install_path && source /home/bigdata/.zshrc && bash install_to_vm_user.sh >install_to_vm_user.out 2>install_to_vm_user.err"

# clean up
rm -rf $LOCAL_TMP_DIR

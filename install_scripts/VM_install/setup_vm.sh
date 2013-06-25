#!/bin/bash


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    VMware automation functions
    
    OPTIONS:
    -h      Show this message
    -i      VM=$VM
    -n      only install the vmware components
    -s      only start the VM and print its ip address
    -t      only suspend the VM
    -k      only set up ssh key login
    -a      only print vm ip address
    -e      only toggle eth0 on VM
EOF
exit
}


#Process the arguments
while getopts hp:v:z:i:nstkae opt
do
    case "$opt" in
        h) usage;;
        i) VM=$OPTARG;;
	n) install_only="True";;
        s) start_only="True";;
        t) suspend_only="True";;
        k) ssh_keys_only="True";;
        a) address_only="True";;
        e) toggle_eth0_only="True";;
    esac
done


install_vmware_components() {
    vmware_player="$1"
    vmware_vix="$2"
    #
    sudo apt-get install build-essential linux-headers-$(uname -r)
    sudo bash "$vmware_player"
    sudo bash "$vmware_vix"
}

start_vm() {
    vmx="$1"
    is_running=$(vmrun -T player list | grep "$vmx")
    if [[ -z $is_running ]]; then
	vmrun -T player start "$vmx" nogui
	# vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" /usr/bin/env bash bin/reset-hadoop.sh
    fi
}

suspend_vm() {
    vmx="$1"
    # vmrun -T player stop "$vmx"
    vmrun -T player suspend "$vmx"
}

print_vm_ip_address() {
    # note: the vmware pdf is slightly wrong about syntax here
    vmx="$1"
    vm_cmd="info-set guestinfo.ip \$(ifconfig eth0 | perl -ne 'print \$1 if m/inet.addr:(\S+)/')"
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" /usr/sbin/vmware-rpctool "$vm_cmd"
    VM_IP=$(vmrun -T player readVariable "$vmx" guestVar ip)
    echo "$VM_IP"
}

set_up_password_login() {
    vmx="$1"
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" \
	/usr/bin/perl -i.bak -pe 's/^#\s+(Password.*)/\$1/' /etc/ssh/ssh_config
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" \
	/usr/sbin/invoke-rc.d ssh restart
}

set_up_ssh_keys() {
    # enable passwordless login
    vmx="$1"
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" \
	/bin/bash -c 'echo \$@ >> /home/bigdata/.ssh/authorized_keys' -- $(cat ~/.ssh/id_rsa.pub)
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" /bin/mkdir /root/.ssh
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" \
	/bin/bash -c 'echo \$@ >> /root/.ssh/authorized_keys' -- $(cat ~/.ssh/id_rsa.pub)
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" \
	/usr/sbin/invoke-rc.d ssh restart
}

toggle_eth0() {
    vmx="$1"
    vmrun -T player -gu root -gp bigdata runProgramInGuest "$vmx" /usr/sbin/service network-manager restart
}

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

# Ensure vmware components present
if [[ -z $(which vmrun) ]]; then
    echo "VMware Player and VIX API must be installed"
    exit
fi

if [[ ! -z $start_only ]]; then
    echo only starting "$VM"
    start_vm "$VM"
    exit
elif [[ ! -z $suspend_only ]]; then
    echo only suspending "$VM"
    suspend_vm "$VM"
    exit
elif [[ ! -z $ssh_keys_only ]]; then
    echo only setting up ssh keys on "$VM"
    set_up_ssh_keys "$VM"
    exit
elif [[ ! -z $address_only ]]; then
    print_vm_ip_address "$VM"
    exit
elif [[ ! -z $toggle_eth0_only ]]; then
    toggle_eth0 "$VM"
    exit
fi


start_vm "$VM"
# set_up_password_login "$VM"
set_up_ssh_keys "$VM"
# give VM extra time to get an IP address
sleep 5

# enable bigdata user to install python pacakges
VM_IP=$(print_vm_ip_address "$VM")
ssh -o StrictHostKeyChecking=no root@$VM_IP chown -R bigdata /opt/anaconda
ssh root@$VM_IP perl -pi.bak -e "'s/^bigdata ALL=\(ALL\) ALL.*/bigdata ALL=\(ALL:ALL\) NOPASSWD: ALL/'" /etc/sudoers

# install local repo of tabular-predDB to VM
bash programmatic_install.sh -i "$VM" -a "$VM_IP"

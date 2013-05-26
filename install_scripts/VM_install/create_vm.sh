#!/bin/bash


#Set the default values
VMwarePlayer=VMware-Player-3.1.4-385536.i386.bundle
VMwareVIX=VMware-VIX-1.12.2-1031769.i386.txt
ZIPPED_VM=debian_6_cdh4_baseline-20130506.zip
VM="Debian 6 64-bit (baseline)/Debian 6 64-bit.vmx"
start_only=
addres_only=


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    VMware automation functions
    
    OPTIONS:
    -h      Show this message
    -p      VMwarePlayer=$VMwarePlayer
    -v      VMwareVIX=$VMwareVIX
    -z      ZIPPED_VM=$ZIPPED_VM
    -i      VM=$VM
    -n      only install the vmware components
    -s      only start the VM and print its ip address
    -t      only termiante the VM
    -a      only print vm ip address
EOF
exit
}


#Process the arguments
while getopts hp:v:z:i:nsta opt
do
    case "$opt" in
        h) usage;;
        p) VMwarePlayer=$OPTARG;;
        v) VMwareVIX=$OPTARG;;
        z) ZIPPED_VM=$OPTARG;;
        i) VM=$OPTARG;;
	n) install_only="True";;
        s) start_only="True";;
        t) terminate_only="True";;
        a) address_only="True";;
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
    vmrun -T player start "$vmx" nogui
}

terminate_vm() {
    vmx="$1"
    vmrun -T player stop "$vmx"
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
}
    
if [[ ! -z $install_only ]]; then
    echo only installing VMware components
    install_vmware_components $VMwarePlayer $VMwareVIX
    exit
elif [[ ! -z $start_only ]]; then
    echo only starting "$VM"
    start_vm "$VM"
    exit
elif [[ ! -z $terminate_only ]]; then
    echo only terminating "$VM"
    terminate_vm "$VM"
    exit
elif [[ ! -z $address_only ]]; then
    print_vm_ip_address "$VM"
    exit
fi


# install vmware components only if not already present
if [[ -z $(which vmrun) ]]; then
    install_vmware_components $VMwarePlayer $VMwareVIX
fi

if [[ ! -f "$VM" ]]; then
    unzip $ZIPPED_VM
fi
start_vm "$VM"
set_up_password_login "$VM"
print_vm_ip_address "$VM"
set_up_ssh_keys "$VM"
 
# enable bigdata user to install python pacakges
VM_IP=$(print_vm_ip_address "$VM")
ssh root@$VM_IP chown -R bigdata /opt/anaconda
ssh root@$VM_IP perl -pi.bak -e "'s/^bigdata ALL=\(ALL\) ALL.*/bigdata ALL=\(ALL:ALL\) NOPASSWD: ALL/'" /etc/sudoers


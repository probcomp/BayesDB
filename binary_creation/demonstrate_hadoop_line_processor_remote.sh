#!/bin/bash

#Set the default values
n_chains=5
n_steps=2
task_timeout=6

# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    Send jobs to hadoop
    
    OPTIONS:
    -h      Show this message
    -t      task_timeout=$task_timeout
    -c      n_chains=$n_chains
    -s      n_steps=$n_steps
EOF
exit
}

# determine if VPN exists
get_vpn_status() {
    echo "$(ifconfig | grep tun)"
}

# make sure you can get to XNET
assert_vpn_status() {
    vpn_status=$(get_vpn_status)
    if [[ -z $(get_vpn_status) ]]; then
        echo "!!!!!!!"
        echo "Can't detect VPN connection"
        echo "Connect to VPN with: sudo vpnc-connect"
        echo "EXITING without sending!!!"
        echo "!!!!!!!"
        exit
    fi
}


# start of code
assert_vpn_status

#Process the arguments
while getopts ht:n:s:v opt
do
    case "$opt" in
        h) usage;;
        t) task_timeout=$OPTARG;;
        n) n_chains=$OPTARG;;
        s) n_steps=$OPTARG;;
        v) verbose="True";;
    esac
done

echo "n_chains=$n_chains"
echo "n_steps=$n_steps"
echo "task_timeout=$task_timeout"
exit

python xnet_utils.py pickle_table_data
python xnet_utils.py write_initialization_files --n_chains $n_chains
cp initialize_input hadoop_input
bash send_hadoop_command.sh
cp myOutputDir/part-00000 initialize_output
python xnet_utils.py link_initialize_to_analyze --initialize_output_filename myOutputDir/part-00000 --n_steps $n_steps
cp analyze_input hadoop_input
bash send_hadoop_command.sh
cp myOutputDir/part-00000 analyze_output

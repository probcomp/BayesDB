#!/bin/bash


# default values
user=sgeadmin
password=


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    Pull down repo from github and run tests via jenkins
    
    OPTIONS:
    -h      Show this message
    -u      user=$user
    -p      password
EOF
exit
}


#Process command line arguments
while getopts hb:u:d: opt
do
    case "$opt" in
        h) usage;;
        u) user=$OPTARG;;
        p) password=$OPTARG;;
    esac
done


# enable password login

perl -pi.bak -e 's/^\s*#*\s*PasswordAuthentication\s+(?:(?:no)|(?:yes))/PasswordAuthentication yes/' /etc/ssh/sshd_config
service ssh reload


# optionally set user's password
if [[ ! -z $password ]]; then
	echo "$user:$password" | chpasswd
fi


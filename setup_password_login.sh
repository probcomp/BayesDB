#!/bin/bash
# USAGE: bash setup_password_login.sh PASSWORD_FOR_SGEADMIN


password=$1
if [[ -z $password ]]; then
    echo "USAGE: bash setup_password_login.sh PASSWORD_FOR_SGEADMIN"
    exit
    echo "fell through"
fi
#
perl -pi.bak -e 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
service ssh reload
echo "sgeadmin:$password" | chpasswd

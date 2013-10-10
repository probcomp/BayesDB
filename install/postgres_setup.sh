#!/bin/bash


# set default values
user=sgeadmin
database=sgeadmin
script=table_setup.sql


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    Set up postgres database
    
    OPTIONS:
    -h      Show this message
    -u      user=$user
    -d      database=$database
    -s      script=$script
EOF
exit
}


#Process the arguments
while getopts hu:d:s: opt
do
    case "$opt" in
        h) usage;;
        u) user=$OPTARG;;
        d) database=$OPTARG;;
        s) script=$OPTARG;;
    esac
done


sudo -u postgres createuser -s jenkins
sudo -u postgres createuser -s $user
sudo -u postgres createdb $database -O $user
sudo -u $user psql $database $user -f $script

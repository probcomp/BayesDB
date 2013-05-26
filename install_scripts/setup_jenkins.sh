#!/bin/bash


# default settings
jenkins_home=/var/lib/jenkins/
jenkins_project=${jenkins_home}/workspace/PredictiveDB
source_dir=/home/bigdata/tabular_predDB/


# install jenkins
wget -q -O - http://pkg.jenkins-ci.org/debian-stable/jenkins-ci.org.key | sudo apt-key add -
sudo echo "deb http://pkg.jenkins-ci.org/debian-stable binary/" >> /etc/apt/sources.list
sudo apt-get update
sudo apt-get install -y jenkins
sudo apt-get update

# copy over the key script that will be run for tests
mkdir -p $jenkins_project
cp ${source_dir}/jenkins_script.sh $jenkins_project
chmod 777 $jenkins_project
chmod 777 ${jenkins_project}/jenkins_script.sh

# run some helper scripts
# let anyone access DB as anyone
bash ${source_dir}/install_scripts/set_postgres_trust.sh
# set up headless matplotlib
mkdir -p ${jenkins_home}/.matplotlib
echo backend: Agg > ${jenkins_home}/.matplotlib/matplotlibrc
# set up password login, set password for jenkins user
bash ${source_dir}/setup_password_login.sh -u jenkins -p jenkins

# make sure jenkins owns everythin
chown -R jenkins $jenkins_home


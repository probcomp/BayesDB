#!/usr/bin/env bash


# test for root
if [[ "$USER" != "root" ]]; then
	echo "$0 must be executed as root"
	exit;
fi


# determine some locations
my_abs_path=$(readlink -f "$0")
my_dirname=$(dirname $my_abs_path)
project_location=$(dirname $(cd $my_dirname && git rev-parse --git-dir))
requirements_filename=$project_location/requirements.txt

# install system dependencies
apt-get build-dep -y python-numpy python-matplotlib
apt-get build-dep -y python-sphinx
apt-get install -y python-pip
apt-get install -y python-dev
# libfreetype6-dev tk-dev libpng12-dev subsumed by 'pip install matplotlib'? 
# 
pip install $options -r $requirements_filename

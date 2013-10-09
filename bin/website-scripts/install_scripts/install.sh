#!/usr/bin/env bash


my_abs_path=$(readlink -f "$0")
my_dirname=$(dirname $my_abs_path)
cd "$my_dirname"

sudo bash install_git_subtree.sh
sudo bash install_heroku_cli.sh
# make sure we have curl
sudo apt-get install -y curl
# can't run this as root, else have difficulties with 'rvm install ruby'
bash install_ruby.sh

#!/bin/bash


# some other changes necessary for running in VM rather than EC2/starcluster
pip install nose==1.1.2
sudo cp /home/bigdata/.zshrc /var/lib/jenkins
sudo chown jenkins /var/lib/jenkins/.zshrc
sudo chsh -s /usr/bin/zsh jenkins
#
# or do chmod 777?
sudo chown -R jenkins /opt/anaconda
# is this even necessary?
sudo ln -s /usr/local/bin/nosetests /usr/bin/nosetest


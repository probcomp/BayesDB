#!/bin/bash


bash install_cxfreeze_user.sh
pip install -r ../../requirements.txt
# hcluster==0.2.0 workaround
pip install --download ./ hcluster==0.2.0
tar xvfz hcluster-0.2.0.tar.gz 
cd hcluster-0.2.0
perl -pi.bak -e "s/input\('Selection \[default=1\]:'\)/2/" setup.py
python setup.py install

mkdir -p ~/.matplotlib
echo backend: Agg > ~/.matplotlib/matplotlibrc


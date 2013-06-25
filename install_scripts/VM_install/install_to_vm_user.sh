#!/bin/bash


bash install_cxfreeze_user.sh
pip install -r ../../requirements.txt
pip install hcluster==0.2.0

mkdir -p ~/.matplotlib
echo backend: Agg > ~/.matplotlib/matplotlibrc


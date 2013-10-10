#!/bin/bash

# install mercurial
#   else can't install git-remote-hg
pip install mercurial==2.6.1

# install git-remote-hg
#   else 'git clone hg::' fails
pip install git-remote-hg==0.1.1

# actually install cxfreeze
git clone hg::https://bitbucket.org/anthony_tuininga/cx_freeze
cd cx_freeze
python setup.py install

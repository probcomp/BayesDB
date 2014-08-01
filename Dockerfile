# Dockerfile for BayesDB project: 
# http://probcomp.csail.mit.edu/bayesdb/
#
# to run as a service in the background localhost port 8008:
#
# docker run -d -p 8008:8008 bayesdb/bayesdb
#

FROM        ubuntu:12.04

MAINTAINER  Aaron Vinson version: 0.2

RUN         apt-get update
RUN         apt-get install -y git dialog wget nano python2.7-dev python-pip libboost1.48-all-dev libfreetype6-dev libatlas-dev libblas-dev liblapack-dev libpng12-dev apt-utils ccache gfortran python-sphinx

# pip install various python libraries
RUN         pip install -U distribute && pip install yolk==0.4.3 && pip install cython==0.17.1 && pip install jsonrpc==1.2 && pip install requests==1.0.3 && pip install Twisted==12.3.0 && pip install pyOpenSSL==0.13 && pip install numpy==1.7.0 && pip install scipy>=0.11.0 && pip install freetype-py==0.4.1 && pip install matplotlib==1.3.1 && pip install patsy && pip install pandas && pip install statsmodels && pip install Sphinx==1.2b1 && pip install prettytable==0.7.2 && pip install pytest>=2.5.1 && pip install cmd2>=0.6.7 && pip install pyparsing>=2.0.1 && pip install ipython>=1.1.0 && pip install pyzmq && pip install tornado==3.1 && pip install nose==1.3.0

# create bayesdb user
RUN         useradd -m -s /bin/bash -d /home/bayesdb -u 1000 -U bayesdb
RUN         usermod -p '$6$qWkoO7mA$gBq9TR5bJvl.0D5xEUmeM3qdMJBJgASrd9N53V3O12NVdQDFzAnZTZjp3qDH8pWsJ/XUe0ORi8QNgBxS45VTB/' bayesdb

WORKDIR     /home/bayesdb

# git clone crosscat
RUN         git clone https://github.com/mit-probabilistic-computing-project/crosscat.git
# pull latest rev
RUN         cd crosscat && git pull

# git clone BayesDB
RUN         git clone https://github.com/mit-probabilistic-computing-project/BayesDB.git
# pull latest rev
RUN         cd BayesDB && git pull

# install crosscat and BayesDB
RUN         cd /home/bayesdb && USER=root bash crosscat/scripts/install_scripts/install.sh
RUN         cd /home/bayesdb && python crosscat/setup.py install
RUN         cd /home/bayesdb && USER=root bash BayesDB/scripts/ubuntu_install.sh
RUN         cd /home/bayesdb/BayesDB && python setup.py install

# remove ubuntu installed numpy versions
RUN         apt-get remove -y python-numpy python-numpy-dbg python3-numpy python3-numpy-dbg

# tweak permissions
RUN         mkdir -p /home/bayesdb/BayesDB
RUN         mkdir /usr/local/lib/python2.7/dist-packages/BayesDB-0.2.0-py2.7.egg/bayesdb/data
RUN         chgrp bayesdb /usr/local/lib/python2.7/dist-packages/BayesDB-0.2.0-py2.7.egg/bayesdb/data
RUN         chmod 775 /usr/local/lib/python2.7/dist-packages/BayesDB-0.2.0-py2.7.egg/bayesdb/data
RUN         chown -R bayesdb:bayesdb /home/bayesdb

# set matplotlib default backend
RUN         echo "backend : agg" > /usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/matplotlibrc

# make a nice readme
RUN         echo "\n\nlogin/pass: bayesdb/bayesdb\n\ntry:\n\npython ~/BayesDB/examples/dha/run_dha_example.py\n" >> readme.txt

# show readme at login
RUN         echo "cat ~/readme.txt" >> .bashrc

EXPOSE      8008

USER        bayesdb
ENV HOME    /home/bayesdb
WORKDIR     /home/bayesdb/BayesDB

RUN         mkdir -p server_logs

CMD         ["python", "-u", "bayesdb/jsonrpc_server.py", ">server_logs/jsonrpc_server.out", "2>server_logs/jsonrpc_server.err"]

#!/usr/bin/env bash


# test for root
if [[ "$USER" != "root" ]]; then
    echo "$0 must be executed as root"
    exit;
fi


apt-get install mercurial

if [[ ! -z ${SUDO_USER} ]]; then
	sudo -i -u $SUDO_USER bash -i -c "cd && hg clone https://bitbucket.org/anthony_tuininga/cx_freeze"
	sudo -i -u $SUDO_USER bash -i -c "workon tabular-predDB && cd && cd cx_freeze && python setup.py install"
fi

#!/usr/bin/env bash


# set default values
CACHED_PACKAGES_DIR=/tmp/CachedPythonPackages
WHICH_HCLUSTER=0.2.0


# print script usage
usage() {
	cat <<EOF
usage: $0 options	
	Set up postgres database
	OPTIONS:

	-h      Show this message
	-c      CACHED_PACKAGES_DIR=$CACHED_PACKAGES_DIR
	-w      WHICH_HCLUSTER=$WHICH_HCLUSTER
EOF
exit
}


#Process the arguments
while getopts hc:w: opt
do
	case "$opt" in
		h) usage;;
		c) CACHED_PACKAGES_DIR=$OPTARG;;
		w) WHICH_HCLUSTER=$OPTARG;;
	esac
done


grep_hcluster=$(yolk -l | grep hcluster)
if [[ -z $grep_hcluster ]]; then
    pip install --no-install --download $CACHED_PACKAGES_DIR hcluster==$WHICH_HCLUSTER
    cd $CACHED_PACKAGES_DIR
    tar xvfz hcluster-$WHICH_HCLUSTER.tar.gz
    cd hcluster-$WHICH_HCLUSTER
    perl -pi.bak -e "s/input\('Selection \[default=1\]:'\)/2/" setup.py
    python setup.py install
fi


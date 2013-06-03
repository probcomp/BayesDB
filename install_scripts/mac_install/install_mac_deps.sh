#!/bin/bash
#
# installs all software dependencies for Mac

ERR_FILE=osxerrs.out

# the directory tabular-predDB must be renamed to tabular_predDB ('-'' to '_')

# we should be in ...tabular-predDB/install_scripts/mac_install
cd ../../tabular_predDB

# We need to install coreutils, because MacOS doesn't support readlink -f. 
# coreutils offers a greadlink (GNU readlink)
echo -ne "Installing coreutils. "
sudo port install coreutils 1>> /dev/null 2> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of coreutils failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

################################################################################
# Install misc requirements
################################################################################
echo -ne "Installing libpng. "
sudo port install libpng 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Installation of libpng failed. Check $ERR_FILE.
	exit
else
	echo "done."
fi

echo -ne "Installing freetype. "
sudo port install freetype 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of freetype failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

# echo -ne "Installing postgres. "
# sudo port install postgresql92 1>> /dev/null 2>> $ERR_FILE
# if [ $? = 1 ]
# then
# 	echo Failed.
# 	echo "Installation of postgres failed. Check $ERR_FILE."
# 	exit
# else
# 	echo "done."
# fi

# echo -ne "Installing postgres server. "
# sudo port install postgresql92-server 1>> /dev/null 2>> $ERR_FILE
# if [ $? = 1 ]
# then
# 	echo Failed.
# 	echo "Installation of postgres server failed. Check $ERR_FILE."
# 	exit
# else
# 	echo "done."
# fi

echo -ne "Installing valgrind. "
sudo port install valgrind 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of valgrind failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

# Python requirements
pip_dir=`which pip`
if [[ -z "$pip_dir" ]]
then
	echo -ne "Installing pip."
	sudo easy_install pip 1>> /dev/null 2>> $ERR_FILE
	if [ $? = 1 ]
	then
		echo Failed.
		echo Installation of pip failed. Check $ERR_FILE.
		exit
	else
		echo "done."
	fi
fi

# set up the virtual environment
echo 
echo "Setting up virtual environment (Python)..."
echo -ne "Installing virtual environment. "
sudo pip install virtualenv 1>> /dev/null 2>> $ERR_FILE && sudo pip install virtualenvwrapper 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of virtualenv failed. Check $ERR_FILE."
	exit
else
	echo "done."
	echo " "
fi

################################################################################
# install Boost 
################################################################################
echo -ne "Installing boost. "
sudo port install boost 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of Boost failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

################################################################################
# set up the virtual environment stuff
################################################################################

# get the current user and make a working directory

USER_HOME=$HOME
WORKING=$USER_HOME/.virtualenvs
PYTHONDIR="$(dirname `pwd`)"

project_name=tabular_predDB
wrapper_script=/usr/local/bin/virtualenvwrapper.sh

# START: POACHED CODE
# The following snippet poached from the original virtualenv_setup.sh
# script:
# ensure virtualenvwrapper is loaded

# make sure that .bashrc exists, if it doesn't make it
if [ -z ${USER_HOME}/.bashrc ]
then
	echo "No .bashrc found. Creating one."
	touch ${USER_HOME}/.bashrc
fi

if [[ -z $(grep WORKON_HOME ${USER_HOME}/.bashrc) ]]; then
    cat -- >> ${USER_HOME}/.bashrc <<EOF
	export PYTHONPATH=${PYTHONPATH}:${USER_HOME}:$PYTHONDIR
	export WORKON_HOME=$WORKING
	source $wrapper_script
EOF
fi

source ${USER_HOME}/.bashrc

# ensure requirements in virtualenv $project_name
has_project=$(workon | grep $project_name)
if [[ -z $has_project ]] ; then
    # readlink -f is not an option on macs so we have to use
    # coreutils greadlink as mentione above -Bax
    my_abs_path=$(greadlink -f "$0")
    project_location=$(dirname $my_abs_path)
    mkvirtualenv $project_name
    cdvirtualenv
    echo "cd $project_location" >> bin/postactivate
    deactivate
    workon $project_name
    sudo pip install numpy==1.7.0 
fi

# echo -ne "Installing front end requirements. "
# sudo pip install -r requirements.txt 1>> /dev/null 2>> $ERR_FILE
# if [ $? = 1 ]
# then
# 	echo Failed.
# 	echo "Installation of front end requirements failed. Check $ERR_FILE."
# 	exit
# else
# 	echo "done."
# fi


echo -ne "Installing cython. "
sudo pip install cython==0.17.1 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of cython failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

echo -ne "Installing numpy. "
sudo pip install numpy==1.7.0 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of numpy failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

echo -ne "Installing matplotlib. "
sudo pip install matplotlib==1.2.0 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of matplotlib failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

echo -ne "Installing freetype-py. "
sudo pip install freetype-py==0.4.1 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of freetype-py failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

# needed for enum_test
echo -ne "Installing scipy. "
sudo pip install scipy 1>> /dev/null 2>> $ERR_FILE
if [ $? = 1 ]
then
	echo Failed.
	echo "Installation of scipy failed. Check $ERR_FILE."
	exit
else
	echo "done."
fi

chown -R $USER $WORKON_HOME

mkdir -p $USER_HOME/.matplotlib && echo backend: Agg > $USER_HOME/.matplotlib/matplotlibrc && chown -R $USER:$USER $USER_HOME/.matplotlib

if [ $? = 1 ]
then
	echo "Something went wrong (see above?)." 
	exit
else
	echo "Installation of dependencies complete."
	#TODO: Follow up messages about next steps
fi

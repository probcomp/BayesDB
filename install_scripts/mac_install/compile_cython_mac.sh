#!/bin/bash
# compiles the cython code


ERR_FILE=osxerrs.out

# get the macports directory
BOOST_DIR="/opt/local/include"

if [ -e "$BOOST_DIR" ]
then
	echo "Detected default MacPorts include directory at /opt/local/include"
else
	if [ -z `which port` ]
	then
		echo "MacPorts not detected. "
		echo "Please install MacPorts from http://www.macports.org/"
	else
		echo "Detected non-standard MacPorts install."
		echo "Please enter the full path to your Boost Headers (For default install this is /opt/local/include)"
		echo -ne "Enter:"

		read BOOST_DIR

		echo " "

		if [ -z "$BOOST_DIR" ]
		then
			echo "$BOOST_DIR does not exist."
			exit
		fi
	fi
fi

# source the virtualenvironment script
source /usr/local/bin/virtualenvwrapper.sh
if [ $? = 1 ]
then
	echo "failed to source virtualenvwrapper.sh."
	echo "Compile failed. Check $ERR_FILE."
	exit
fi

echo -ne "Compiling..."

workon tabular_predDB

if [ $? = 1 ]
then
	echo "workon command failed."
	echo "Compile failed. Check $ERR_FILE."
	exit
fi

cd cython_code

sudo make -f Makefile.mac 1>> /dev/null 2>> $ERR_FILE

if [ $? = 1 ]
then
	echo Failed.
	echo "Compile failed. Check $ERR_FILE."
	exit
else
	echo "done."
	# echo "Run Test (y/n)?"
	# read run_test
fi
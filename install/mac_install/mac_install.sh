#!/bin/bash
#
# CrossCat Mac OSX installation script
# Currently only works for Mac OS 10.7 and 10.8 (Lion and Mountain Lion). It 
# does not appear to work on Snow Leopard.
#
# Installation requires XCode with command line tools and MacPorts.
# XCode can be got from the app store. The command line tools are installed 
# through XCode's preferences menu.
# MacPorts can be downloaded from http://www.macports.org/
# This script assumes that the user has a default macports install with all 
# packages installed to /opt/local

# make all scripts executable if they are not already 
if [ ! -x install_mac_deps.sh ]
then
	chmod +x install_mac_deps.sh
fi

if [ ! -x compile_cython_mac.sh ]
then
	chmod +x compile_cython_mac.sh
fi

if [ ! -x init_postgres_mac.sh ]
then
	chmod +x init_postgres_mac.sh
fi

# Check for OSX version
OSX_VERSION=`sw_vers -productVersion | grep -o '[0-9]' | awk '{i++}i==3'`
if [ "$OSX_VERSION" -lt 7 ]
then
	echo "This script does not currently work on OSX below 10.7 (Lion)."
	exit
fi

# check for xcode
if [ -z `which xcodebuild` ]
then
	echo "Installation requires XCode."	
	echo "Please install XCode from the App Store."
	echo "Once you have installed XCode, please install the command line tools from XCode\'s preferences menu."
	exit
fi

# check for maports
WHICH_PORT=`which port`
if [ -z "$WHICH_PORT" ]
then
	echo "Installation requires MacPorts (http://www.macports.org/)."
	exit
fi


echo " "
echo "tabular_predDB mac OSX setup:"
echo -e "\t1. Install backend dependencies."
echo -e "\t2. Compile Cython and C++ code."
# echo -e "\t3. Set up PostgresDB."
echo " "
echo -ne "Enter choice: "

read user_input

echo " "

case "$user_input" in
	1) 
		sudo ./install_mac_deps.sh
		;;
	2) 
		sudo ./compile_cython_mac.sh
		;;
	# 3)
	# 	./init_postgres_mac.sh
	# 	;;
	*) 
		echo "Invalid input."
		exit
		;;
		
esac
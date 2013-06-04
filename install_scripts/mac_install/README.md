# Mac OSX installation

## Notes

- Works only on OS 10.7 and 10.8.
- Requires XCode with command line utilities
- Requires [MacPorts](http://www.macports.org/)
- Assumes that MacPorts uses the default directory `/opt/local/`
- Uses `bash` instead of default login shell (see below)

## Installation Instructions

Make the installation script executable

     chmod +x mac_install.sh

Run the script

     ./mac_install.sh

Select 1 to install the backend dependencies.
This will install all necessary libraries, create a virtual environment, and update `.bashrc`

Once this has completed, run the script again and select 2 to compile the code.
Any time you wish to compile the code, simply run the script and select 2.

There is also the makefile in the `tabular_predDB/cython_code` directory which can be run with

	make -f Makefile.mac

## Running code

**At this time all code must be run from bash.**

1. Enter a bash session by entering `bash` in terminal.
2. To access the virtual environment enter `workon tabular_predDB`
3. You are now in the `tabular-predDB` directory and ready to run code!

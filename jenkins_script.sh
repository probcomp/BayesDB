#!/bin/bash

# default values
branch="master"
user="jenkins"
home_dir="/var/lib/jenkins/"

# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    Pull down repo from github and run tests via jenkins
    
    OPTIONS:
    -h      Show this message
    -b      set the branch to run (default=$branch)
    -u      set the user to install virtualenv under (default=$user)
    -h      set the dir to install virtualenv under (default=$home_dir)
EOF
exit
}


#Process command line arguments
while getopts hb:u:d: opt
do
    case "$opt" in
        h) usage;;
        b) branch=$OPTARG;;
	u) user=$OPTARG;;
	d) home_dir=$OPTARG;;
    esac
done

echo "jenkins_script.sh:"
echo "user: $user"
echo "branch: $branch"
echo "home_dir: $home_dir"

# Remove old source, and checkout newest source from master.
source /var/lib/jenkins/.bashrc
rm -rf tabular_predDB
git clone --depth=1 https://probcomp-reserve:metropolis1953@github.com/mit-probabilistic-computing-project/tabular-predDB.git tabular_predDB --branch $branch
cd tabular_predDB

# If the virtualenv isn't set up, do that.
if [ ! -e /var/lib/jenkins/.virtualenvs ]
then
  bash -i install_scripts/virtualenv_setup.sh $user $home_dir >virtualenv.out 2>virtualenv.err
  source /var/lib/jenkins/.bashrc
fi
workon tabular_predDB

# Build and run tests. WORKSPACE is set by jenkins to /var/
export PYTHONPATH=$PYTHONPATH:$WORKSPACE
cd $WORKSPACE/tabular_predDB
make tests
make cython
cd tabular_predDB/tests
python /usr/bin/nosetests --with-xunit cpp_unit_tests.py cpp_long_tests.py test_middleware.py test_sampler.py

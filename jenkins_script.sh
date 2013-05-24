#!/bin/bash

# Remove old source, and checkout newest source from master.
source /var/lib/jenkins/.bashrc
rm -rf tabular_predDB
git clone --depth=1 https://probcomp-reserve:metropolis1953@github.com/mit-probabilistic-computing-project/tabular-predDB.git tabular_predDB
cd tabular_predDB
WHICH_BRANCH=$(python -c 'import sys; sys.path.append("/var/lib/jenkins/workspace/PredictiveDB/tabular_predDB"); import tabular_predDB.settings as S; print S.git.branch')
git checkout $WHICH_BRANCH

# If the virtualenv isn't set up, do that.
if [ ! -e /var/lib/jenkins/.virtualenvs ]
then
  bash -i install_scripts/virtualenv_setup.sh jenkins /var/lib/jenkins >virtualenv.out 2>virtualenv.err
fi
workon tabular_predDB

# Build and run tests. WORKSPACE is set by jenkins to /var/
export PYTHONPATH=$WORKSPACE
cd $WORKSPACE/tabular_predDB
make tests
make cython
cd tabular_predDB/tests
python /usr/bin/nosetests --with-xunit cpp_unit_tests.py cpp_long_tests.py test_middleware.py

USER=$1
if [[ $# -eq 2 ]]; then
    USER_HOME=$2
else
    USER_HOME=/home/${USER}/
fi
WORKON_HOME=${USER_HOME}/.virtualenvs
# FIXME: should take project_name as an argument passed from settings.py somehow
project_name=tabular_predDB
wrapper_script=/usr/local/bin/virtualenvwrapper.sh

# ensure virtualenvwrapper is loaded
if [[ -z $(grep WORKON_HOME ${USER_HOME}/.bashrc) ]]; then
    cat -- >> ${USER_HOME}/.bashrc <<EOF
export PYTHONPATH=${PYTHONPATH}:${USER_HOME}/${project_name}
export WORKON_HOME=$WORKON_HOME
source $wrapper_script
EOF
fi

source ${USER_HOME}/.bashrc

# ensure requirements in virtualenv $project_name
has_project=$(workon | grep $project_name)
if [[ -z $has_project ]] ; then
    # BEWARE: readlink doesn't work on macs
    my_abs_path=$(readlink -f "$0")
    project_location="$(dirname $my_abs_path)/.."
    mkvirtualenv $project_name
    cdvirtualenv
    echo "cd $project_location" >> bin/postactivate
    deactivate
    workon $project_name
    pip install numpy==1.7.0
fi

pip install -r ../requirements.txt

chown -R $USER $WORKON_HOME

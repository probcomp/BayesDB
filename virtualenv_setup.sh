project_name=tabular_predDB
WORKON_HOME=$HOME/.virtualenvs
wrapper_script=/usr/local/bin/virtualenvwrapper.sh

# ensure virtualenv
which_virtualenv=$(which virtualenv)
if [ -z $which_virtualenv ]; then
    sudo pip install virtualenv
fi

# ensure virtualenvwrapper
if [ ! -f $wrapper_script ]; then
    sudo pip install virtualenvwrapper
    cat -- >> ~/.bashrc <<EOF
export WORKON_HOME=$WORKON_HOME
source $wrapper_script
EOF
    source ~/.bashrc
fi

# ensure requirements in virtualenv $project_name
has_project=$(workon | grep $project_name)
if [ -z $has_project ] ; then
    # BEWARE: readlink doesn't work on macs
    my_abs_path=$(readlink -f "$0")
    project_location=$(dirname $my_abs_path)
    mkvirtualenv $project_name
    cdvirtualenv
    echo "cd $project_location" >> bin/postactivate
    deactivate
    workon $project_name
    pip install -r requirements.txt
fi

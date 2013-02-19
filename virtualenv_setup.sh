project_name=crosscat
WORKON_HOME=$HOME/.virtualenvs

# ensure virtualenv
which_virtualenv=$(which virtualenv)
if [ -z $which_virtualenv ]; then
    sudo pip install virtualenv
    sudo pip install virtualenvwrapper
    cat -- >> ~/.bashrc <<EOF
export WORKON_HOME=$WORKON_HOME
source /usr/local/bin/virtualenvwrapper.sh
EOF
    source ~/.bashrc
fi

has_project=$(workon | grep $project_name)
if [ -z $has_project ] ; then
    # readlink doesn't work on macs
    my_abs_path=$(readlink -f "$0")
    project_location=$(dirname $my_abs_path)
    mkvirtualenv $project_name
    cdvirtualenv
    echo "cd $project_location" >> bin/postactivate
    deactivate
    workon $project_name
    pip install -r requirements.txt

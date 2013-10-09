# determine where this script is; must be inside a repo
my_abs_path=$(readlink -f "$0")
script_location=$(dirname $my_abs_path)
git_dir=$(cd $script_location && git rev-parse --git-dir)
if [[ $? -ne 0 ]]; then
	echo "Couldn't find enclosing git dir.  Are you sure you're in a project dir?"
	exit
fi
project_dir=$(dirname $git_dir)
project_name=$(basename $project_dir)


# assume app_name is dir name enclosing .git if argument is not passed
app_name=$project_name
if [[ ! -z $1 ]]; then
	app_name=$1
fi


# go to the git repo so heroku can be set as remote
cd $project_dir


# make sure logged into heroku
# possibly requires interaction: must enter credentials on command line if not logged in
heroku auth:whoami


# must be run from repo to push
heroku create $app_name > heroku_create.out
heroku config:set --app $app_name BUILDPACK_URL=https://github.com/ddollar/heroku-buildpack-multi.git


# heroku remote will automatically be added to git repo
# repo will be seomthing like calm-journey-XXXX
# add as remote from another repo with:
# > heroku git:remote -a calm-journey-XXXX
# can detect app_name with:
# > app_name=$(grep Creating heroku_create.out | awk '{print $2}' | awk -F'.' '{print $1}')

# inspect what the repo is with
# > git remote -v | grep heroku

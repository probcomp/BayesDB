# determine where you are; must be inside a repo
my_abs_path=$(readlink -f "$0")
script_location=$(dirname $my_abs_path)
git_dir=$(cd $script_location && git rev-parse --git-dir)
if [[ $? -ne 0 ]]; then
	echo "Couldn't find enclosing git dir.  Are you sure you're in a project dir?"
	exit
fi
project_dir=$(dirname $git_dir)
project_name=$(basename $project_dir)


# assume app_name is dir name enclosing .git unless argument is passed
app_name=$project_name
if [[ ! -z $1 ]]; then
	app_name=$1
fi


# assume website dir is $project_dir/website unless argument is passed
website_dir=$project_dir/website
if [[ ! -z $2 ]]; then
	website_dir=$2
fi


# set up a local git repo of just the website content
cd $website_dir
git init
git add .
git commit -a -m 'initial commit'
heroku git:remote -a $app_name


# make sure you can push to heroku
keyfile=~/.ssh/id_rsa
if [[ ! -f $keyfile ]]; then
	ssh-keygen -t rsa -P "" -f $keyfile
fi
heroku keys:add $keyfile.pub


# may need to append --force
git push heroku master


# would like to remove .git
# but don't want to accidentally remove project repo accidentally
# rm -rf .git

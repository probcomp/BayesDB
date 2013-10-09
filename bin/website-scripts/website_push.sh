#!/bin/bash


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


# assume website dir is $project_dir/website unless argument is passed
# website dir must be relative to project_dir
website_dir=website
if [[ ! -z $1 ]]; then
	website_dir=$1
fi


branch_name=master
if [[ ! -z $2 ]]; then
	branch_name=$2
fi


# cd to project_dir so relative path is used
cd $project_dir


# Push the subtree (force)
git push heroku `git subtree split --prefix $website_dir $branch_name`:master --force

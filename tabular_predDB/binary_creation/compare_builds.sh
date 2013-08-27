#!/bin/bash


# set deafults
HDFS_DIR="$(python -c 'import tabular_predDB.settings as S; print S.Hadoop.default_hdfs_dir')"
HDFS_URI="$(python -c 'import tabular_predDB.settings as S; print S.Hadoop.default_hdfs_uri')"
first_branch="master"
second_branch="engine_optimization"


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    VMware automation functions
    
    OPTIONS:
    -h      Show this message
    -f      first_branch=$first_branch
    -s      second_branch=$second_branch
    -d      HDFS_DIR=$HDFS_DIR
    -u      HDFS_URI=$HDFS_URI
EOF
exit
}


#Process the arguments
while getopts hf:s:d:u: opt
do
    case "$opt" in
        h) usage;;
        f) first_branch=$OPTARG;;
        s) second_branch=$OPTARG;;
	d) HDFS_DIR=$OPTARG;;
        u) HDFS_URI=$OPTARG;;
    esac
done


make_binary_name() {
	which_branch=$1
	# build_date=$(date +"%Y%M%d")
	build_date=20130826
	which_engine_binary="${HDFS_DIR}/hadoop_line_processor_${which_branch}_${build_date}.jar"
	echo $which_engine_binary
}


# make sure environment is correct
# export PYTHONPATH=~/tabular_predDB:$PYTHONPATH
repo_dir=$(python -c 'import tabular_predDB.settings as S; print S.path.this_repo_dir')
cd $repo_dir
sudo bash install_scripts/my_vpnc_connect.sh


# build both branches
for which_branch in $first_branch $second_branch; do
	git checkout $which_branch
	git pull
	cd $repo_dir
	make clean && make cython
	# FIXME: should break here if build fails
	cd tabular_predDB/binary_creation
	which_engine_binary=$(make_binary_name $which_branch)
	bash build_and_push.sh -b $which_engine_binary -d $HDFS_DIR -u $HDFS_URI


# runtime analysis
cd $repo_dir
git checkout master
cd tabular_predDB/timing_analysis
for which_branch in $first_branch $second_branch; do
	which_engine_binary=$(make_binary_name $which_branch)
	python automated_runtime_tests.py -do_remote --which_engine_binary $which_engine_binary \
	       --num_rows_list 1000 --num_cols_list 16 32 --num_splits_list 2 4 &
	sleep 30
done
wait


# convergence analysis
cd $repo_dir
git checkout master
cd tabular_predDB/convergence_analysis
for which_branch in $first_branch $second_branch; do
	which_engine_binary=$(make_binary_name $which_branch)
	python automated_convergence_tests.py -do_remote --which_engine_binary $which_engine_binary \
		--num_rows_list 400 --num_cols_list 32 --num_clusters_list 5 --num_splits_list 4 \
		--max_mean_list 1 --n_steps 100 -do_plot &
	sleep 30
done
wait


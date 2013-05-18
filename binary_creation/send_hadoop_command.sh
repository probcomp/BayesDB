#!/bin/bash


#Set the default values
num_map_tasks=
task_timeout_in_ms=600000
input_filename=hadoop_input
verbose=

# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    Send jobs to hadoop
    
    OPTIONS:
    -h      Show this message
    -t      task_timeout_in_ms=$task_timeout_in_ms
    -n      num_map_tasks=$num_map_tasks
    -i      input_filename=$input_filename
    -v      verbose=False
EOF
exit
}

get_num_lines() {
    filename=$1
    num_lines=$(wc -l $filename | awk '{print $1}')
    echo $num_lines
}

# determine if VPN exists
get_vpn_status() {
    echo "$(ifconfig | grep tun)"
}

# make sure you can get to XNET
assert_vpn_status() {
    vpn_status=$(get_vpn_status)
    if [[ -z $(get_vpn_status) ]]; then
        echo "!!!!!!!"
        echo "Can't detect VPN connection"
        echo "Connect to VPN with: sudo vpnc-connect"
        echo "EXITING without sending!!!"
        echo "!!!!!!!"
        exit
    fi
}

#Process the arguments
while getopts ht:n:i:v opt
do
    case "$opt" in
        h) usage;;
        t) task_timeout_in_ms=$OPTARG;;
        n) num_map_tasks=$OPTARG;;
        i) input_filename=$OPTARG;;
        v) verbose="True";;
    esac
done

# num_map_tasks is one per line unless set on command line
if [[ -z $num_map_tasks ]]; then
    num_map_tasks=$(get_num_lines $input_filename)
fi

echo "task_timeout_in_ms=$task_timeout_in_ms"
echo "num_map_tasks=$num_map_tasks"
echo "input_filename=$input_filename"
echo "verbose=$verbose"

# make sure you can get to XNET
assert_vpn_status

# setup
WHICH_BINARY="hadoop_line_processor"
HDFS_DIR="/user/bigdata/SSCI/test_remote_streaming/"
JOBTRACKER_URI="xd-jobtracker.xdata.data-tactics-corp.com:8021"
HDFS_URI="hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
WHICH_HADOOP_JAR="/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar"

# FIXME: should check for ${WHICH_BINARY} existence on HDFS
# FIXME: should check for hadoop_input, table_data.pkl.gz existence on local FS

# prep local FS
rm -rf myOutputDir
# prep HDFS
# assume jar already on HDFS
hadoop fs -fs "$HDFS_URI" -rm -r -f "${HDFS_DIR}"myOutputDir 2>/dev/null
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"hadoop_input 2>/dev/null
# hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"table_data.pkl.gz
hadoop fs -fs "$HDFS_URI" -put hadoop_input "${HDFS_DIR}"
# hadoop fs -fs "$HDFS_URI" -put table_data.pkl.gz "${HDFS_DIR}"

# run
$HADOOP_HOME/bin/hadoop jar "$WHICH_HADOOP_JAR" \
    -D mapred.task.timeout="${task_timeout_in_ms}" \
    -D mapred.map.tasks="${num_map_tasks}" \
    -archives "${HDFS_URI}${HDFS_DIR}${WHICH_BINARY}.jar" \
    -fs "$HDFS_URI" -jt "$JOBTRACKER_URI" \
    -input "${HDFS_URI}${HDFS_DIR}hadoop_input" \
    -output "${HDFS_URI}${HDFS_DIR}myOutputDir/" \
    -mapper ${WHICH_BINARY}.jar/${WHICH_BINARY} \
    -reducer /bin/cat \
    -file hadoop_input \
    -file table_data.pkl.gz \
    -cmdenv LD_LIBRARY_PATH=./${WHICH_BINARY}.jar/:$LD_LIBRARY_PATH

#  -D mapred.reduce.tasks=0 \
#    -reducer /bin/cat \

# get results
hadoop fs -fs "$HDFS_URI" -get "${HDFS_DIR}"myOutputDir

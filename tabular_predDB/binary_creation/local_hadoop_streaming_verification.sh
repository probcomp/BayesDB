#!/bin/bash


HADOOP_FS="hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
HADOOP_JT="xd-jobtracker.xdata.data-tactics-corp.com:8021"
HDFS_OUTPUT_DIR="/user/bigdata/SSCI/test_remote_streaming/myOutputDir"
HDFS_INPUT="/user/bigdata/SSCI/test_remote_streaming/words"


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    VMware automation functions
    
    OPTIONS:
    -h      Show this message
    -f      HADOOP_FS=$HADOOP_FS
    -j      HADOOP_JT=$HADOOP_JT
    -o      HDFS_OUTPUT_DIR=$HDFS_OUTPUT_DIR
    -i      HDFS_INPUT=$HDFS_INPUT
EOF
exit
}


#Process the arguments
while getopts hf:j:o:i: opt
do
    case "$opt" in
        h) usage;;
        f) HADOOP_FS=$OPTARG;;
        j) HADOOP_JT=$OPTARG;;
        o) HDFS_OUTPUT_DIR=$OPTARG;;
        i) HDFS_INPUT=$OPTARG;;
    esac
done


# from guest OS
CDH4_2_0_JAR=/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.2.0.jar
CDH4_1_2_JAR=/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar
WHICH_JAR=$CDH4_2_0_JAR
if [[ ! -f $WHICH_JAR ]]; then
  WHICH_JAR=$CDH4_1_2_JAR
fi

# do once

hadoop fs -fs "$HADOOP_FS" -mkdir /user/bigdata/SSCI/test_remote_streaming
hadoop fs -fs "$HADOOP_FS" -put /usr/share/dict/words /user/bigdata/SSCI/test_remote_streaming
hadoop fs -fs "$HADOOP_FS" -rm -r "$HDFS_OUTPUT_DIR" > hadoop_streaming_verification.out
#
hadoop jar $WHICH_JAR -fs "$HADOOP_FS" -jt "$HADOOP_JT" -input "$HDFS_INPUT" -output "$HADOOP_FS/$HDFS_OUTPUT_DIR" -mapper /bin/cat -reducer /usr/bin/wc >> hadoop_streaming_verification.out

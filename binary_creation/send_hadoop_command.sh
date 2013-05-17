#log into VM, must use -X or cx_freeze complains
# vm_ip=192.168.1.10
# ssh -X bigdata@$vm_ip

# make sure you can get to XNET
if [[ -z $(ifconfig | grep tun) ]]; then
  echo "Can't detect VPN connection: '-z \$(ifconfig | grep tun)' is True"
  echo "Connect to VPN with: sudo vpnc-connect"
  echo "EXITING without sending!!!"
  exit
  # sudo vpnc-connect
fi

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
hadoop fs -fs "$HDFS_URI" -rm -r -f "${HDFS_DIR}"myOutputDir
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"hadoop_input
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"table_data.pkl.gz
hadoop fs -fs "$HDFS_URI" -put hadoop_input "${HDFS_DIR}"
hadoop fs -fs "$HDFS_URI" -put table_data.pkl.gz "${HDFS_DIR}"

# run
$HADOOP_HOME/bin/hadoop jar "$WHICH_HADOOP_JAR" \
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

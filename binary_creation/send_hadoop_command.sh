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

if [[ -z $1 ]]; then
  echo "USAGE: bash build_and_push.sh WHICH_BINARY"
  echo "EXITING without sending!!!"
  exit
fi

# setup
HDFS_DIR="/user/bigdata/SSCI/test_remote_streaming/"
JOBTRACKER_URI="xd-jobtracker.xdata.data-tactics-corp.com:8021"
HDFS_URI="hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
WHICH_HADOOP_JAR="/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar"

# prep local FS
rm -rf myOutputDir
printf "1\n2" > seed_list.txt
# prep HDFS
# assume jar already on HDFS
hadoop fs -fs "$HDFS_URI" -rm -r -f "${HDFS_DIR}"myOutputDir
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"seed_list.txt
hadoop fs -fs "$HDFS_URI" -put seed_list.txt "${HDFS_DIR}"

# run
$HADOOP_HOME/bin/hadoop jar "$WHICH_HADOOP_JAR" \
  -archives "${HDFS_URI}${HDFS_DIR}"${WHICH_BINARY}#${WHICH_BINARY} \
  -fs "$HDFS_URI" -jt "$JOBTRACKER_URI" \
  -D mapred.reduce.tasks=0 \
  -input "${HDFS_URI}${HDFS_DIR}seed_list.txt" \
  -output "${HDFS_URI}${HDFS_DIR}myOutputDir/" \
  -mapper ${WHICH_BINARY}/${WHICH_BINARY} \
  -file hadoop_input.pkl.gz \
  -cmdenv LD_LIBRARY_PATH=./${WHICH_BINARY}/:$LD_LIBRARY_PATH

# get results
hadoop fs -fs "$HDFS_URI" -get "${HDFS_DIR}"myOutputDir

#log into VM, must use -X or cx_freeze complains
# vm_ip=192.168.1.10
# ssh -X bigdata@$vm_ip

# make sure you can get to XNET
if [[ -z $(ifconfig | grep tun) ]]; then
  sudo vpnc-connect
fi

# setup
CODE_LOC=~/
export PYTHONPATH=$CODE_LOC:$PYTHONPATH
HDFS_DIR="/user/bigdata/SSCI/test_remote_streaming/"
JOBTRACKER_URI="xd-jobtracker.xdata.data-tactics-corp.com:8021"
HDFS_URI="hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
WHICH_JAR="/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar"

# create binary
cd $CODE_LOC/tabular_predDB/binary_creation
python setup.py build
(cd build/exe.linux-x86_64-2.7 && jar cvf ../../single_map.jar *)

# prep local FS
rm -rf myOutputDir
echo "1\n2" > seed_list.txt
# prep HDFS
hadoop fs -fs "$HDFS_URI" -rm -r -f "${HDFS_DIR}"myOutputDir
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"single_map.jar
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"seed_list.txt
hadoop fs -fs "$HDFS_URI" -put single_map.jar "${HDFS_DIR}"
hadoop fs -fs "$HDFS_URI" -put seed_list.txt "${HDFS_DIR}"

# run
$HADOOP_HOME/bin/hadoop jar "$WHICH_JAR" \
  -archives "${HDFS_URI}${HDFS_DIR}single_map.jar#single_map" \
  -fs "$HDFS_URI" -jt "$JOBTRACKER_URI" \
  -D mapred.reduce.tasks=0 \
  -input "${HDFS_URI}${HDFS_DIR}seed_list.txt" \
  -output "${HDFS_URI}${HDFS_DIR}myOutputDir/" \
  -mapper single_map.sh \
  -file single_map.sh -file dha.csv \
  -cmdenv LD_LIBRARY_PATH=./single_map/:$LD_LIBRARY_PATH

# get results
hadoop fs -fs "$HDFS_URI" -get "${HDFS_DIR}"myOutputDir

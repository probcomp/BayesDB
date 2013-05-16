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
CODE_LOC=~/
export PYTHONPATH=$CODE_LOC:$PYTHONPATH
WHICH_BINARY=$1
HDFS_DIR="/user/bigdata/SSCI/test_remote_streaming/"
HDFS_URI="hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"

# create binary
cd $CODE_LOC/tabular_predDB/binary_creation
python setup.py build
(cd build/exe.linux-x86_64-2.7 && jar cvf ../../${WHICH_BINARY}.jar *)

# prep HDFS
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"${WHICH_BINARY}.jar
hadoop fs -fs "$HDFS_URI" -put ${WHICH_BINARY}.jar "${HDFS_DIR}"

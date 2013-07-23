#!/bin/bash


HDFS_DIR="/user/bigdata/SSCI/"
# HDFS_URI="hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
HDFS_URI="hdfs://10.1.93.51:8020/"

# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    VMware automation functions
    
    OPTIONS:
    -h      Show this message
    -b      WHICH_BINARY=$WHICH_BINARY
    -d      HDFS_DIR=$HDFS_DIR
    -u      HDFS_URI=$HDFS_URI
EOF
exit
}


#Process the arguments
while getopts hb:d:u: opt
do
    case "$opt" in
        h) usage;;
        b) WHICH_BINARY=$OPTARG;;
	d) HDFS_DIR=$OPTARG;;
        u) HDFS_URI=$OPTARG;;
    esac
done


# determine if VPN exists
get_vpn_status() {
    this_dir="$(dirname $0)"
    rel_dir="$this_dir/../python_utils/"
    echo "$(python ${rel_dir}/xnet_utils.py assert_vpn_is_connected)"
}

# make sure you can get to XNET
assert_vpn_status() {
    vpn_status=$(get_vpn_status)
    if [[ ! -z $(get_vpn_status) ]]; then
        echo "!!!!!!!"
        echo "Can't detect VPN connection"
        echo "Connect to VPN with: sudo vpnc-connect"
        echo "EXITING without sending!!!"
        echo "!!!!!!!"
        exit
    fi
}

# make sure you know what to call the jar file
if [[ -z $WHICH_BINARY ]]; then
    echo "USAGE: bash build_and_push.sh -b <WHICH_BINARY>"
    echo "WHICH_BINARY is a required argument!!!"
    echo "EXITING without sending!!!"
    exit
fi

# setup
this_dir="$(dirname $(readlink -f $0))"
CODE_REL_DIR="$this_dir/../.."
export PYTHONPATH=$CODE_REL_DIR:$PYTHONPATH

# create binary
cd $CODE_REL_DIR/tabular_predDB/binary_creation
rm -rf build
python setup.py build >build.out 2>build.err
# FIXME: find a better way to do this; works on 20130307 VM to use on XDATA cluster
LARGEST_LAPACK_LITE=$(locate lapack_lite | xargs ls -al | sort -k 4 | head -n 1 | awk '{print $NF}')
if [[ ! -z $LARGEST_LAPACK_LITE ]]; then
    TARGET_LAPACK_LITE=build/exe.linux-x86_64-2.7/numpy.linalg.lapack_lite.so
    cp $LARGEST_LAPACK_LITE $TARGET_LAPACK_LITE
fi
(cd build/exe.linux-x86_64-2.7 && jar cvf ../../${WHICH_BINARY}.jar *)

# prep HDFS
hadoop fs -fs "$HDFS_URI" -rm "${HDFS_DIR}"${WHICH_BINARY}.jar
hadoop fs -fs "$HDFS_URI" -mkdir "${HDFS_DIR}"
hadoop fs -fs "$HDFS_URI" -put ${WHICH_BINARY}.jar "${HDFS_DIR}"

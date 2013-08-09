#!/usr/bin/env bash


# test for root
if [[ "$USER" != "root" ]]; then
    echo "$0 must be executed as root"
    exit;
fi


# set up for vpnc
apt-get install vpnc

if [[ ! -z "$1" && ! -z "$SUDO_USER" ]]; then
    # verify hadoop operations: requires interaction
    # connect to VPN: must insert login credentials
    vpnc-connect --gateway xdata.data-tactics-corp.com --id xdata && \
    	route add -net 10.1.93.0 netmask 255.255.255.0 dev tun0 && \
    	route add -net 10.1.92.0 netmask 255.255.255.0 dev tun0 && \
    	route add -net 10.1.90.0 netmask 255.255.255.0 dev tun0 && \
    	route del -net 0.0.0.0 tun0
    
    # can you get to the computer cluster jobtracker?
    wget 10.1.92.53:50030 && rm index.html
    
    # verify hdfs connectivity
    $(grep "export JAVA_HOME" /home/$SUDO_USER/.bashrc)
    hadoop fs -ls /user/bigdata
    
    # verify sending hadoop job
    hadoop fs -put /usr/share/dict/words /tmp/wordcount_input
    hadoop fs -rmr /tmp/wordcount_output
    WHICH_JAR=/usr/share/doc/hadoop-0.20-mapreduce/examples/hadoop-examples.jar
    hadoop jar $WHICH_JAR wordcount /tmp/wordcount_input /tmp/wordcount_output
    
    # verify streaming functionality
    WHICH_JAR=/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.2.0.jar
    hadoop fs -rm -r /tmp/wordcount_output
    hadoop jar $WHICH_JAR -input /tmp/wordcount_input -output /tmp/wordcount_output -mapper /bin/cat -reducer /usr/bin/wc

    # don't exit in different state than you entered
    vpnc-disconnect
fi

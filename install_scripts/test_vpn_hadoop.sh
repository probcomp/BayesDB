if [[ -z $(ifconfig | grep tun0) ]]; then
	echo "no device tun0 present; are you connected to the VPN?"
	exit
fi

if [[ $(whoami) != "bigdata" ]]; then
	echo "$0 must be run as user 'bigdata'"
	exit
fi

# can you get to the computer cluster jobtracker?
wget 10.1.92.53:50030 -O - >/dev/null

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

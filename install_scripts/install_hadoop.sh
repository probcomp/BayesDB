#!/usr/bin/env bash


# test for root
if [[ "$USER" != "root" ]]; then
    echo "$0 must be executed as root"
    exit;
fi

# purge the old stuff
apt-get purge -y hadoop-0.20
perl -i.bak -ne 'print if ! m/cdh3/' /etc/apt/sources.list

# set up to get the new stuff
cat -- > /etc/apt/sources.list.d/cloudera-cdh4.list <<EOF
deb [arch=amd64] http://archive.cloudera.com/cdh4/ubuntu/lucid/amd64/cdh lucid-cdh4.2.0 contrib
deb-src http://archive.cloudera.com/cdh4/ubuntu/lucid/amd64/cdh lucid-cdh4.2.0 contrib
EOF
#
apt-get update
# yes, twice
apt-get update

# get the new stuff
apt-get install -y --force-yes hadoop-0.20-conf-pseudo

# configure some network/address stuff
perl -i.orig -pe 's/localhost/10.1.92.51/' /etc/hadoop/conf/core-site.xml
perl -i.orig -pe 's/localhost/10.1.92.53/' /etc/hadoop/conf/mapred-site.xml
perl -i.orig -pe 's/search ec2.internal/# search ec2.internal/' /etc/resolv.conf

# make sure openjdk-6-jdk is available
apt-get install -y openjdk-6-jdk

# determine which JAVA_HOME to use
for JAVA_HOME in /usr/lib/jvm/java-6-openjdk/ \
	/usr/lib/jvm/java-6-openjdk-amd64/ \
	NONE
do
	if [[ -d $JAVA_HOME ]]; then
		break
	fi
done
if [[ "$JAVA_HOME" == "NONE" ]]; then
	echo "No valid JAVA_HOME"
	exit
fi

# set up JAVA_HOME for sudo user
if [[ ! -z ${SUDO_USER} ]]; then
	cat -- >> /home/$SUDO_USER/.bashrc <<EOF
export JAVA_HOME=$JAVA_HOME
EOF
fi


# if you have hadoop, you'll want cx_freeze
bash install_cx_freeze.sh

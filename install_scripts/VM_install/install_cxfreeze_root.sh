# enable debian package installation from ppa
#   else can't install newer version of git
cd
wget http://blog.anantshri.info/content/uploads/2010/09/add-apt-repository.sh.txt
cp add-apt-repository.sh.txt /usr/sbin/add-apt-repository
chmod o+x /usr/sbin/add-apt-repository
add-apt-repository ppa:git-core/ppa
apt-get update

# remove necessity for manual intervention
apt-get purge -y apt-listchanges

# install newer version of git
#   else can't install git-remote-hg
apt-get install -y git

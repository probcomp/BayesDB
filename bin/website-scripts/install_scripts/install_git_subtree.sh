# per http://engineeredweb.com/blog/how-to-install-git-subtree/
cd && git clone https://github.com/git/git.git
cd git/contrib/subtree
make
sudo install -m 755 git-subtree /usr/lib/git-core

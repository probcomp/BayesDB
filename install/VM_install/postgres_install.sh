#!/bin/bash


# remove, otherwise seem to have a conflict
apt-get purge -y postgresql-8.4
apt-get purge -y postgresql-client-8.4

# per http://www.postgresql.org/download/linux/debian/
echo deb http://apt.postgresql.org/pub/repos/apt/ squeeze-pgdg main > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
sudo apt-key add -
sudo apt-get update
apt-get install -y postgresql-9.1

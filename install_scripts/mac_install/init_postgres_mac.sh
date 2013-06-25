#!/bin/bash

# not currently working

# finish up the macports postgresql install
sudo mkdir -p /opt/local/var/db/postgresql92/defaultdb
sudo chown -R postgres:postgres /opt/local/var/db/postgresql92/defaultdb
sudo su postgres -c '/opt/local/lib/postgresql92/bin/initdb -D /opt/local/var/db/postgresql92/defaultdb'

# start the server
sudo su postgres -c '/opt/local/lib/postgresql92/bin/postgres -D /opt/local/var/db/postgresql92/defaultdb'

# create a user and a database
sudo su postgres -c '/opt/local/lib/postgresql92/bin/createuser -s sgeadmin'
sudo su postgres -c '/opt/local/lib/postgresql92/bin/createdb sgeadmin -O sgeadmin'

# Set up postgres SQL
sudo su sgeadmin -c '/opt/local/lib/postgresql92/bin/psql -f ../table_setup.sql'
# sudo su sgeadmin -c 'psql -f table_setup.sql'
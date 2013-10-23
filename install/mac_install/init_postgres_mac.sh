#!/bin/bash

# not currently working

# finish up the macports postgresql install
sudo mkdir -p /opt/local/var/db/postgresql92/defaultdb
sudo chown -R postgres:postgres /opt/local/var/db/postgresql92/defaultdb
sudo su postgres -c '/opt/local/lib/postgresql92/bin/initdb -D /opt/local/var/db/postgresql92/defaultdb'

# start the server
sudo su postgres -c '/opt/local/lib/postgresql92/bin/postgres -D /opt/local/var/db/postgresql92/defaultdb'

# create a user and a database
sudo su postgres -c '/opt/local/lib/postgresql92/bin/createuser -s $(whoami)'
sudo su postgres -c '/opt/local/lib/postgresql92/bin/createdb $(whoami) -O $(whoami)'

# Set up postgres SQL
sudo su $(whoami) -c '/opt/local/lib/postgresql92/bin/psql -f ../table_setup.sql'
# sudo su $(whoami) -c 'psql -f table_setup.sql'

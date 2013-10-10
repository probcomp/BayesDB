#!/bin/bash


# make it easier for everyone to access tables
# could be a security issue
perl -i.bak -pe 's/peer/trust/' /etc/postgresql/9.1/main/pg_hba.conf
/etc/init.d/postgresql reload

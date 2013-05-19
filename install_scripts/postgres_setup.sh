sudo -u postgres createuser -s sgeadmin
sudo -u postgres createdb sgeadmin -O sgeadmin
sudo -u sgeadmin psql -f /home/sgeadmin/tabular_predDB/table_setup.sql

sudo -u postgres createuser -s jenkins
sudo -u postgres createuser -s sgeadmin
sudo -u postgres createdb sgeadmin -O sgeadmin
sudo -u sgeadmin psql -f /home/sgeadmin/tabular_predDB/install_scripts/table_setup.sql

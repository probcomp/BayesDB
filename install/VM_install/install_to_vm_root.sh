#!/bin/bash


bash postgres_install.sh
bash ../set_postgres_trust.sh

bash install_cxfreeze_root.sh

bash install_debian_packages.sh

bash ../install_boost.sh

cd .. && bash postgres_setup.sh -u bigdata

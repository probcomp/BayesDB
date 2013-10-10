if [ $# -eq 1 ]; then
    WEB_RESOURCES_DIR=$1
else
    WEB_RESOURCES_DIR=www
fi
mkdir -p $WEB_RESOURCES_DIR
cd $WEB_RESOURCES_DIR
mkdir -p server_logs
python -m SimpleHTTPServer 8000 \
    >server_logs/SimpleHTTPServer.out 2>server_logs/SimpleHTTPServer.err &

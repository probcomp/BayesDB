WEB_RESOURCES_DIR=$1
mkdir -p $WEB_RESOURCES_DIR
cd $WEB_RESOURCES_DIR
python -m SimpleHTTPServer 8000 \
    >SimpleHTTPServer.out 2>SimpleHTTPServer.err &

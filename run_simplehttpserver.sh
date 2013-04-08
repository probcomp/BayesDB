cd /home/sgeadmin/tabular_predDB
mkdir -p images
cd images
python -m SimpleHTTPServer 8000 >SimpleHTTPServer.out 2>SimpleHTTPServer.err &

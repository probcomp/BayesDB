tabular-predDB
==============

tabular predictive database

Instructions for building
-------------------------------------------------
    > cd /path/to/tabular-predDB
    > make

Running server
---------------------------
    > cd /path/to/tabular-predDB
    > make cython
    > python server_jsonrpc.py >server_jsonrpc.out 2>server_jsonrpc.err &
    > # test with 'python stub_client_jsonrpc.py

Running tests
---------------------------
    > # capture stdout, stderr separately
    > cd /path/to/tabular-predDB
    > make tests >tests.out 2>tests.err


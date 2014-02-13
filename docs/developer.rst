Developer Reference
===================

Running Tests
~~~~~~~~~~~~~
There are two current testing suites in the tests directory: test_engine.py and test_client.py. The client tests test end-to-end functionality: they take a full BQL query string and make sure output is generate. The engine tests are more like unit tests in that they call methods on engine, and assert that it gives appropriate output.

Run them with::

  py.test test_engine.py test_client.py
  py.test test_engine.py test_client.py -k-slow # Skip slow tests
  py.test test_engine.py # Only run engine tests
  py.test test_engine.py -k test_simulate # Only run the function called test_simulate in test_engine.py

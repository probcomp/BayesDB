BayesDB
==============

BayesDB, a Bayesian database, lets users query the probable implications of their data as easily as a SQL database lets them query the data itself. Using the built-in Bayesian Query Language (BQL), users with no statistics training can solve basic data science problems, such as detecting predictive relationships between variables, inferring missing values, simulating probable observations, and identifying statistically similar database entries.

BayesDB is suitable for analyzing complex, heterogeneous data tables with up to tens of thousands of rows and hundreds of variables. No preprocessing or parameter adjustment is required, though experts can override BayesDB's default assumptions when appropriate.

BayesDB's inferences are based in part on CrossCat, a new, nonparametric Bayesian machine learning method, that automatically estimates the full joint distribution behind arbitrary data tables.

# Installation

### VM

We provide a VirtualBox VM ([Get the VM and VM_README here](http://probcomp.csail.mit.edu/bayesdb/#Download)) for small scale testing of BayesDB.

**Note**: The VM is only meant to provide an out-of-the-box usable system setup.  Its resources are limited and large jobs will fail due to memory errors.  To run larger jobs, increase the VM resources or install directly to your system.

### Local
BayesDB depends on CrossCat, so first install CrossCat by following its local installation instructions [here](https://github.com/mit-probabilistic-computing-project/crosscat/blob/master/README.md).

BayesDB can be installed locally with:

    git clone https://github.com/mit-probabilistic-computing-project/BayesDB.git
    cd BayesDB
    sudo python setup.py install

If you have trouble with matplotlib, you should try switching to a different backend. Open a python prompt ($ python):

    import matplotlib
    matplotlib.matplotlib_fname()

Then, edit the file at the path that was outputted, changing 'backend' to another one of the available values, until the matplotlib errors go away. Good ones to try are GTKAgg and Agg.

# Documentation

[Website](http://probcomp.csail.mit.edu/bayesdb)

[Documentation](http://probcomp.csail.mit.edu/bayesdb/docs)

# Example

run\_dha\_example.py ([github](https://github.com/mit-probabilistic-computing-project/BayesDB/blob/master/examples/dha/run_dha_example.py)) is a basic example of analysis using BayesDB.  For a first test, run the following from inside the top level BayesDB dir

    python examples/dha/run_dha_example.py

# License

[Apache License, Version 2.0](https://github.com/mit-probabilistic-computing-project/bayesdb/blob/master/LICENSE)







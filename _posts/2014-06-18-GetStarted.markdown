---
layout: default
title: Get Started
tagline: Download. Install. Explore.
---
	
###Download
BayesDB uses [CrossCat](https://github.com/mit-probabilistic-computing-project/crosscat) as an inference engine so we install that first.

	$ git clone https://github.com/mit-probabilistic-computing-project/crosscat.git
	$ sudo bash crosscat/scripts/install_scripts/install.sh
	$ sudo python crosscat/setup.py install
	
Clone BayesDB from [Github](www.github.com). 

    $ git clone https://github.com/mit-probabilistic-computing-project/BayesDB.git

###Install
    $ cd BayesDB
    $ sudo python setup.py install

Alternatively, you can avoid the need to install BayesDB to your system python

    $ sudo python setup.py develop
	
In this case you'll need to add the BayesDB directory to your `PYTHONPATH`.		

###Explore
	
BayesDB ships with a few example datasets with pre-computed models ready to go. Just navigate to an example directory and spool up an interactive python session.

	$ cd examples/dha
	$ python
	
Now we'll create a table, load in some models and start exploring the data.

	>>> from bayesdb.client import Client
	>>> client = Client()
	>>> client('CREATE BTABLE dha FROM dha.csv;')
	>>> client('LOAD MODEL dha_models.pkl.gz INTO dha;')
	>>> client('ESTIMATE PAIRWISE DEPENDENCE PROBABILIY FROM dha SAVE TO dha_z.png;')
	
You've just created a dependence probability matrix, which shows you the probability of dependence between each pair of columns, and saved it to `dha_z.png`.

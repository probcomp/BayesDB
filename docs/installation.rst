Installing BayesDB
==================

To get started using BayesDB as quickly as possible, the :ref:`docker-install` is recommended. If you are interested in installing BayesDB to perform large-scale analyses, please use either the :ref:`manual-install` or :ref:`ec2-install` (coming soon).

.. _docker-install:

Docker Installation
~~~~~~~~~~~~~~~
BayesDB can be accessed via a `community-contributed Docker container <https://registry.hub.docker.com/u/bayesdb/bayesdb/>`_. Install instructions for Docker can be found `here <https://docs.docker.com/installation/#installation>`_.

Once docker has been installed and configured enter the following command in your Unix/Linux terminal to download and install the Docker container (this will take a few minutes)::

	docker pull bayesdb/bayesdb

.. _manual-install:

Manual Installation
~~~~~~~~~~~~~~~~~~~
BayesDB depends on CrossCat, so first install CrossCat by following its local installation instructions `here <https://github.com/mit-probabilistic-computing-project/crosscat/blob/master/README.md>`_.

BayesDB can be installed locally with::

    git clone https://github.com/mit-probabilistic-computing-project/BayesDB.git
    cd BayesDB
    sudo python setup.py install

If you have trouble with matplotlib, you should try switching to a different backend. Open a python prompt ($ python)::

    import matplotlib
    matplotlib.matplotlib_fname()

Then, edit the file at the path that was outputted, changing 'backend' to another one of the available values, until the matplotlib errors go away. Good ones to try are GTKAgg and Agg.
    
			    

.. _ec2-install:

Amazon EC2 Starcluster Install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Coming soon!

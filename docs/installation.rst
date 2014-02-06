Installing BayesDB
==================

To get started using BayesDB as fast as possible, the :ref:`vm-install` is recommended. Note that the VM is not suited to memory intensive tasks, but it is perfect as a way to try BayesDB that is guaranteed to work out-of-the-box. If you are interested in installing BayesDB to perform any medium to large scale analyses, please use either the :ref:`manual-install` or :ref:`ec2-install` (coming soon).

.. _vm-install:

VM Installation
~~~~~~~~~~~~~~~
**NOTE**: The VM is only meant to provide an out-of-the-box usable system setup.  Its resources are limited and large jobs will cause memory errors.  To run larger jobs, increase the VM resources or install directly to your system.

Overview
--------

After downloading the VM, working with the VM for the first time requires

#. Uncompressing the VM
#. Importing the VM
#. Starting the VM
#. Logging into the VM

Uncompressing the VM
--------------------

* Mac: double click the tgz file
* Linux: right click the tgz file, select extract here

Importing the VM
----------------

#. double click the extracted ovf file
#. click import in the VirtualBox GUI

See `VirtualBox Manual <https://www.virtualbox.org/manual/ch01.html#ovf>`_ for more info

Starting the VM
---------------

* click Start in the VirtualBox GUI

Logging into the VM
-------------------

At the prompt in the VM GUI

* login/username: bayesdb
* password: bayesdb

Log in via SSH
--------------

You can log in via ssh with (tested on Ubuntu and Mac OSX)::

    > ssh-keygen -f ~/.ssh/known_hosts -R [localhost]:2222
    > ssh -i vm_guest_id_rsa -p 2222 -o StrictHostKeyChecking=no bayesdb@localhost


.. _manual-install:

Manual Installation
~~~~~~~~~~~~~~~~~~~
**Note: Only Ubuntu is currently supported. A Mac OS X install may be coming soon.**

BayesDB depends on CrossCat, so first install CrossCat by following its local installation instructions `here <https://github.com/mit-probabilistic-computing-project/crosscat/blob/master/README.md>`_.

BayesDB can be installed locally on Ubuntu systems with::

    git clone https://github.com/mit-probabilistic-computing-project/BayesDB.git
    sudo bash BayesDB/install/install.sh
    cd BayesDB && PYTHONPATH=$PYTHONPATH:$(pwd)

Don't forget to add BayesDB to your python path.  For bash, this can be accomplished with::

    cd BayesDB
    cat -- >> ~/.bashrc <<EOF
    export PYTHONPATH=\$PYTHONPATH:$(pwd)
    EOF

If you have trouble with matplotlib, you should try switching to a different backend. Open a python prompt ($ python)::

    import matplotlib
    matplotlib.matplotlib_fname()

Then, edit the file at the path that was outputted, changing 'backend' to another one of the available values, until the matplotlib errors go away. Good ones to try are GTKAgg and Agg.
    
			    

.. _ec2-install:

Amazon EC2 Starcluster Install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Coming soon!

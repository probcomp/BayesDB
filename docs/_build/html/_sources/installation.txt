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

See [VirtualBox Manual](https://www.virtualbox.org/manual/ch01.html#ovf) for more info

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
ihadsf

.. _ec2-install:

Amazon EC2 Starcluster Install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Coming soon!

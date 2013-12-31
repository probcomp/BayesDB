#!/usr/bin/python
import os
from distutils.core import setup, Extension

ext_modules = []

packages = ['bayesdb', 'bayesdb.tests']
setup(
        name='BayesDB',
        version='0.1',
        author='MIT.PCP',
        author_email = 'bayesdb@mit.edu',
        url='probcomp.csail.mit.edu/bayesdb',
        long_description='BayesDB',
        packages=packages,
        package_dir={'bayesdb':'bayesdb/'},
        ext_modules=ext_modules,
        )

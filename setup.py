#!/usr/bin/env python

from distutils.core import setup

setup(
    name='BayesDB',
    version='0.1',
    author='MIT Probabilistic Computing Project',
    author_email = 'bayesdb@mit.edu',
    url='probcomp.csail.mit.edu/bayesdb',
    long_description='BayesDB',
    packages=['bayesdb', 'bayesdb.tests']
)

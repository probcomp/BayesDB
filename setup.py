import os


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


# make sure cwd is correct
this_file = os.path.abspath(__file__)
this_dir = os.path.split(this_file)[0]
os.chdir(this_dir)


setup(
    name='BayesDB',
    version='0.2.0',
    author='MIT Probabilistic Computing Project',
    author_email = 'bayesdb@mit.edu',
    url='probcomp.csail.mit.edu/bayesdb',
    long_description='BayesDB',
    packages=['bayesdb', 'bayesdb.tests'],
    install_requires=['jsonrpc', 'requests', 'Twisted', 'pyOpenSSL',
                      'numpy', 'scipy', 'matplotlib>=1.2.0',
                      'Sphinx', 'pytest',
                      'prettytable', 'cmd2', 'pyparsing>=2.0.1',
                      'ipython', 'pandas>=0.13',
                      ],
    license='Apache License, Version 2.0',
    entry_points = """
                   [console_scripts]
                   bql = bayesdb.bql:run_command_line
                   """
                   
)

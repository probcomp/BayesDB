try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='BayesDB',
    version='0.2.0',
    author='MIT Probabilistic Computing Project',
    author_email = 'bayesdb@mit.edu',
    url='probcomp.csail.mit.edu/bayesdb',
    long_description='BayesDB',
    packages=['bayesdb', 'bayesdb.tests'],
    install_requires=['jsonrpc', 'requests', 'Twisted', 'pyOpenSSL',
                      'numpy', 'scipy', 'matplotlib', 'hcluster',
                      'Sphinx', 'pytest',
                      'prettytable', 'cmd2', 'pyparsing',
                      'ipython', 'pandas'],
    license='Apache License, Version 2.0',
    entry_points = """
                   [console_scripts]
                   bql = bayesdb.bql:run_command_line
                   """
                   
)

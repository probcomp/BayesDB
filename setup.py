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
                      'numpy', 'scipy', 'matplotlib>=1.2.0', 'hcluster',
                      'Sphinx', 'pytest',
                      'prettytable', 'cmd2', 'pyparsing>=2.0.1',
                      'ipython', 'pandas>=0.7.1', # this pandas version required by patsy
                      'patsy', 'seaborn'], # patsy required by seaborn
    license='Apache License, Version 2.0',
    entry_points = """
                   [console_scripts]
                   bql = bayesdb.bql:run_command_line
                   """
                   
)

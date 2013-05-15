# A simple setup script to create an executable using matplotlib.
#
# test_matplotlib.py is a very simple matplotlib application that demonstrates
# its use.
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application


import sys
#
import cx_Freeze


excludes = []
includes = [
    'tabular_predDB.python_utils.data_utils',
    'tabular_predDB.python_utils.plot_utils',
    'tabular_predDB.python_utils.file_utils',
    'tabular_predDB.cython_code.State',
    'numpy',
    'pylab',
    'matplotlib.backends.backend_qt4agg',
    ]
path = list(sys.path)
path.append('/home/bigdata/single_map/')

buildOptions = dict(
        excludes = excludes,
        includes = includes,
        path = path,
        compressed = True,
)

executables = [
        cx_Freeze.Executable("single_map.py", base = None)
]

cx_Freeze.setup(
        name = "single_map",
        version = "0.1",
        description = "initialize and transition a single markov chain",
        executables = executables,
        options = dict(build_exe = buildOptions))


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

buildOptions = dict(
        excludes = excludes,
        includes = includes,
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


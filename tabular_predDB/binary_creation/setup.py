# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application


import sys
#
import cx_Freeze


excludes = [
    'FixTk',
    'Tkconstants',
    'Tkinter',
    ]
includes = [
    'tabular_predDB.python_utils.data_utils',
    'tabular_predDB.python_utils.file_utils',
    'tabular_predDB.python_utils.timing_test_utils',
    'tabular_predDB.LocalEngine',
    'tabular_predDB.HadoopEngine',
    'tabular_predDB.cython_code.State',
    'tabular_predDB.python_utils.xnet_utils',
    'tabular_predDB.python_utils.general_utils',
    'tabular_predDB.python_utils.sample_utils',
    'numpy',
    # 'tabular_predDB.python_utils.plot_utils',
    # 'pylab',
    # 'matplotlib.backends.backend_qt4agg',
    ]

buildOptions = dict(
        excludes = excludes,
        includes = includes,
        compressed = False,
)

executables = [
        cx_Freeze.Executable("hadoop_line_processor.py", base = None)
]

cx_Freeze.setup(
        name = "hadoop_line_processor",
        version = "0.1",
        description = "process arbitrary engine commands on hadoop",
        executables = executables,
        options = dict(build_exe = buildOptions))

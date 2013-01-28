from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
  name = 'Demos',
  ext_modules=[
        # Extension("boost_matrix_test",
        #       sources=["boost_matrix_test.pyx",
        #                ],
        #       include_dirs=["../include/CrossCat/"],
        #       language="c++"),
        # Extension("continuous_component_model_test",
        #       sources=["continuous_component_model_test.pyx",
        #                "../src/utils.cpp",
        #                "../src/numerics.cpp",
        #                "../src/RandomNumberGenerator.cpp",
        #                "../src/ComponentModel.cpp",
        #                "../src/ContinuousComponentModel.cpp"],
        #       include_dirs=["../include/CrossCat/"],
        #       language="c++"),
        Extension("State",
              sources=["State.pyx",
                       "../src/utils.cpp",
                       "../src/numerics.cpp",
                       "../src/RandomNumberGenerator.cpp",
                       "../src/DateTime.cpp",
                       "../src/State.cpp",
                       "../src/View.cpp",
                       "../src/Cluster.cpp",
                       "../src/ComponentModel.cpp",
                       "../src/ContinuousComponentModel.cpp"],
              include_dirs=["../include/CrossCat/"],
              language="c++"),
    ],
  cmdclass = {'build_ext': build_ext},

)

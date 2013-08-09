#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import sys
import os
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext


virtual_env_dirs = [
	'/opt/anaconda/',
	'/var/lib/jenkins/.virtualenvs/tabular_predDB/',
	'~/.virtualenvs/tabular_predDB/',
	'~/.virtualenvs/tabular-predDB/',
	]
numpy_rel_dir = "lib/python2.7/site-packages/numpy/core/include/"
numpy_include_full_dirs = [
	os.path.join(virtual_env_dir, numpy_rel_dir)
	for virtual_env_dir in virtual_env_dirs
	]
numpy_include_full_dirs = [
	os.path.expanduser(numpy_include_full_dir)
	for numpy_include_full_dir in numpy_include_full_dirs
	]
valid_dirs = filter(os.path.isdir, numpy_include_full_dirs)
if len(valid_dirs) == 0:
    error_message = 'none of numpy_include_full_dirs exist: %s\n' \
        % ', '.join(numpy_include_full_dirs)
    sys.stderr.write(error_message)
    sys.exit()

rel_dir = '../../cpp_code/'
include_dirs = [
	os.path.join(rel_dir, 'include/CrossCat'),
	os.environ.get('BOOST_ROOT', '.'),
        ]
include_dirs.extend(valid_dirs)

setup(
    name = 'Demos',
    ext_modules=[
        Extension("ContinuousComponentModel",
                  sources=["ContinuousComponentModel.pyx",
                           os.path.join(rel_dir, "src/utils.cpp"),
                           os.path.join(rel_dir, "src/numerics.cpp"),
                           os.path.join(rel_dir, "src/RandomNumberGenerator.cpp"),
                           os.path.join(rel_dir, "src/ComponentModel.cpp"),
                           os.path.join(rel_dir, "src/ContinuousComponentModel.cpp"),
                           ],
                  include_dirs=include_dirs,
                  language="c++"),
        Extension("MultinomialComponentModel",
                  sources=["MultinomialComponentModel.pyx",
                           os.path.join(rel_dir, "src/utils.cpp"),
                           os.path.join(rel_dir, "src/numerics.cpp"),
                           os.path.join(rel_dir, "src/RandomNumberGenerator.cpp"),
                           os.path.join(rel_dir, "src/ComponentModel.cpp"),
                           os.path.join(rel_dir, "src/MultinomialComponentModel.cpp"),
                           ],
                  include_dirs=include_dirs,
                  language="c++"),
        Extension("State",
                  sources=["State.pyx",
                           os.path.join(rel_dir, "src/utils.cpp"),
                           os.path.join(rel_dir, "src/numerics.cpp"),
                           os.path.join(rel_dir, "src/RandomNumberGenerator.cpp"),
                           os.path.join(rel_dir, "src/DateTime.cpp"),
                           os.path.join(rel_dir, "src/State.cpp"),
                           os.path.join(rel_dir, "src/View.cpp"),
                           os.path.join(rel_dir, "src/Cluster.cpp"),
                           os.path.join(rel_dir, "src/ComponentModel.cpp"),
                           os.path.join(rel_dir, "src/MultinomialComponentModel.cpp"),
                           os.path.join(rel_dir, "src/ContinuousComponentModel.cpp"),
                           ],
                  include_dirs=include_dirs,
                  language="c++",
                  ),
        ],
    cmdclass = {'build_ext': build_ext},
    )

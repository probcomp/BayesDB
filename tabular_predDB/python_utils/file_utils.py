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
import cPickle
import gzip
import os
import sys


def is_gz(filename):
    ext = os.path.splitext(filename)[-1]
    return ext == '.gz'

def is_pkl(filename):
    if is_gz(filename):
        filename = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[-1]
    return ext == '.pkl'

def my_open(filename):
    opener = open
    if is_gz(filename):
        opener = gzip.open
    return opener

def pickle(variable, filename, dir=''):
    full_filename = os.path.join(dir, filename)
    opener = my_open(full_filename)
    with opener(full_filename, 'wb') as fh:
        cPickle.dump(variable, fh)

def unpickle(filename, dir=''):
    full_filename = os.path.join(dir, filename)
    opener = my_open(full_filename)
    with opener(full_filename, 'rb') as fh:
        variable = cPickle.load(fh)
    return variable

def rm_local(path, DEBUG=False):
    cmd_str = 'rm -rf %s'
    cmd_str %= path
    if DEBUG:
        print cmd_str
    else:
        os.system(cmd_str)
    return

def ensure_dir(dir):
  try:
    os.makedirs(dir)
  except Exception, e:
    if e.strerror.upper()=='FILE EXISTS':
      pass
    else:
      sys.stderr.write('Could not create dir: %s\n' % dir)
      raise e
  return

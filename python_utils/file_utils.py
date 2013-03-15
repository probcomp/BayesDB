import cPickle
import gzip
import os

def my_open(filename):
    ext = os.path.splitext(filename)[-1]
    opener = open
    if ext == 'gz':
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

import cPickle
import gzip
import os

def my_open(filename):
    ext = os.path.splitext(filename)[-1]
    opener = open
    if ext == 'gz':
        opener = gzip.open
    return opener

def pickle(variable, filename):
    opener = my_open(filename)
    with opener(filename, 'wb') as fh:
        cPickle.dump(variable, fh)

def unpickle(filename):
    opener = my_open(filename)
    with opener(filename, 'rb') as fh:
        variable = cPickle.load(fh)
    return variable

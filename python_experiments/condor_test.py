
import os
import condor

condor.DEBUG = True

def f():
     return 1
def g():
     return f()
def h(x, y):
    return x + y

### test write job ###

condor.write_job('/tmp/', g, ())
os.system('/tmp/job.py')

### test call ###

condor.call(g)
condor.call(h, -1, 2)



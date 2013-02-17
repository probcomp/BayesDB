
### test write job ###

import os
import condor

def f():
     return 1
def g():
     print f()

condor.write_job('/tmp/', g, ())
os.system('python /tmp/job.py')

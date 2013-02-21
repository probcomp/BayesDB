"""
Package for distributed computing on a Condor cluster
Attempts to mirror some functionality of PiCloud's cloud package
"""

"""
Copyright (c) 2013 Peter Krafft.  All rights reserved.

email: pkrafft@mit.edu

The condor package is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation; either version 2.1 of the
License, or (at your option) any later version.

This package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this package; if not, see 
http://www.gnu.org/licenses/lgpl-2.1.html
"""

"""
This package might do a few odd things. It assumes you are running it
from the Condor cluster. It assumes the local packages you need are in
your current working directory. It creates a directory to keep track
of the jobs it creates. Also, certain variables that exist in the
calling script will not be copied to the cluster. For example, lists
are not currently supported. Booleans, integers, float, and strings
that do not begin with "__" are supported. (though floats may not
work properly. The status functionality is limited. It only tells you
whether a job is "done" or "unknown", which doesn't match picloud's
API. The condor cluster can take a few seconds to tell you the status of
a job, so it is not worth implementing the full functionality.
"""


import pickle
import marshal
import types
import os
import sys
import stat
import inspect

out_dir = os.getcwd() + '/jobs/'
if not os.path.exists(out_dir): 
    os.makedirs(out_dir)

DEBUG = False

def call(func, *args, **kwargs):

    if not callable(func):
        raise TypeError( 'condor.call first argument (%s) is not callable'  % (str(func) ))
    
    try: 
        f = open(out_dir + 'last_id', 'r')
        job_id = str(int(f.readline()) + 1)
        f.close()
    except:
        job_id = '0'
    f = open(out_dir + 'last_id', 'w')
    f.write(job_id)
    f.close()

    job_dir = out_dir + job_id + '/'

    try:
        os.makedirs(job_dir)
    except OSError as e:
        raise CondorPythonError('Job ' + job_id + 
                                ' already exists! Seek help.')
                
    write_job(job_dir, func, args)
    write_description(job_dir, job_id)

    if DEBUG:
        os.system(job_dir + 'job.py')
    else:
        os.system('condor_submit ' + job_dir + 'description')
    
    return job_id

def result(jids):
    if isinstance(jids, collections.Iterable):
        results = []
        for jid in jids:
            results += [get_result(jid)]
    else:
        results = get_result(jids)
    return results

def status(jids):
    if isinstance(jids, collections.Iterable):
        statuses = []
        for jid in jids:
            statuses += [get_status(jid)]
    else:
        statuses = get_status(jids)
    return statuses


########################
### helper functions ###
########################

def get_status(jid):
    try open(job_dir + jid + '/success'):
        return 'done'
    except IOError:
        return 'unknown'

def get_result(jid):
    out_file = out_dir + jid + '/stdout.txt'
    f = open(out_file)
    result = f.readlines()
    f.close()
    return result

def write_description(job_dir, job_id):
    desc_f = open(job_dir + 'description', 'w')
    desc_f.write('GetEnv = True\n')
    desc_f.write('Universe = vanilla\n')
    desc_f.write('Notification = Error\n')
    desc_f.write('Executable = ' + job_dir + 'job.py\n')
    desc_f.write('Log = /tmp/job.' + os.environ['USER'] + '.' +
                 job_id + '.log\n')
    desc_f.write('Error = ' + job_dir + 'stderr.txt\n')
    desc_f.write('Output = ' + job_dir + 'stdout.txt\n')
    desc_f.write('queue 1\n')
    desc_f.close()

def write_job(job_dir, func, args):
    
    name = job_dir + 'job.py'
    job_f = open(name, 'w')

    job_f.write('#! /usr/bin/env python\n')
    job_f.write('import os, sys, marshal, types, pickle\n')
    job_f.write('os.chdir(\'' + os.getcwd() + '\')\n') 
    job_f.write('sys.path.append(\'' + os.getcwd() + '\')\n')

    write_dependencies(job_f, job_dir)
    write_func(job_f, job_dir, func, args)

    job_f.write('open(\'' + job_dir + 'success\',\'w\').close()')

    job_f.close()
    st = os.stat(name)
    os.chmod(name, st.st_mode | stat.S_IEXEC)


def write_func(job_f, job_dir, func, args):
    
    arg_f = open(job_dir + 'args.pkl', 'wb')
    pickle.dump(args, arg_f)
    arg_f.close()
    
    job_f.write('arg_f = open(\'' + job_dir + 'args.pkl\')\n')
    job_f.write('args = pickle.load(arg_f)\n')
    job_f.write('arg_f.close()\n')

    job_f.write('print ' + func.__name__ + '(*args)')
            
def write_dependencies(job_f, job_dir):

    func_num = 0
    main = __import__("__main__")

    for name in dir(main):

        val = getattr(main, name)

        if isinstance(val, types.ModuleType):
            job_f.write('import ' + val.__name__ + ' as ' + name + '\n')

        VarTypes = (types.BooleanType, types.IntType,
                    types.FloatType)
        if isinstance(val, VarTypes):
            job_f.write(name + ' = ' + str(val) + '\n')

        if isinstance(val, types.StringType):
            if not val[0:2] == '__':
                job_f.write(name + ' = \'' + val + '\'\n')

        if isinstance(val, types.FunctionType):
            job_f.write(inspect.getsource(val))
    
class CondorPythonError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

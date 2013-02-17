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

import pickle
import marshal
import types
import os
import sys

out_dir = os.getcwd() + '/jobs/'
if not os.path.exists(out_dir): 
    os.makedirs(out_dir)

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

    desc_f = open(job_dir + 'description', 'w')

def write_job(job_dir, func, args):
    
    job_f = open(job_dir + 'job.py', 'w')

    job_f.write('import os, sys, marshal, types, pickle\n')
    job_f.write('os.chdir(\'' + os.getcwd() + '\')\n') 
    job_f.write('sys.path.append(\'' + os.getcwd() + '\')\n')

    write_dependencies(job_f, job_dir)
    write_func(job_f, job_dir, func, args)

    job_f.close()


def write_func(job_f, job_dir, func, args):
    
    arg_f = open(job_dir + 'args.pkl', 'wb')
    pickle.dump(args, arg_f)
    arg_f.close()
    
    job_f.write('arg_f = open(\'' + job_dir + 'args.pkl\')\n')
    job_f.write('args = pickle.load(arg_f)\n')
    job_f.write('arg_f.close()\n')

    job_f.write('def _wrapper(args):\n')
    job_f.write('    return ' + func.__name__ + '(*args)\n')
    job_f.write('_wrapper(args)')
            
def write_dependencies(job_f, job_dir):

    func_num = 0
    main = __import__("__main__")

    for name in dir(main):

        val = getattr(main, name)

        if isinstance(val, types.ModuleType):
            job_f.write('import ' + val.__name__ + ' as ' + name + '\n')

        if isinstance(val, types.FunctionType):
            
            f_name = job_dir + 'func_' + str(func_num)
            func_num += 1

            src = marshal.dumps(val.func_code)
            
            func_f = open(f_name, 'w')
            func_f.write(src)
            func_f.close()
            
            job_f.write('func_f = open(\'' + f_name + '\')\n')
            job_f.write('src = marshal.load(func_f)\n')
            job_f.write('func_f.close()\n')
            job_f.write(name + ' = types.FunctionType(src, globals(),\'' + name + '\')\n')
    
class CondorPythonError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

import subprocess
import os

def test_view():
    run_shell_command('test_view')

def test_view_speed():
    run_shell_command('test_view_speed')

def test_state():
    run_shell_command('test_state')

def run_shell_command(name):
    p = subprocess.Popen(['%s/%s' % (os.path.dirname(os.path.abspath(__file__)), name)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    retcode = p.wait()
    out = p.stdout.read()
    err = p.stderr.read()
    if len(err) > 0:
        fail(err)

import subprocess
import os

def test_component_model():
    run_shell_command('test_component_model')

def test_continuous_component_model():
    run_shell_command('test_continuous_component_model')

def test_multinomial_component_model():
    run_shell_command('test_multinomial_component_model')

def test_cluster():
    run_shell_command('test_cluster')

def run_shell_command(name):
    p = subprocess.Popen(['%s/%s' % (os.path.dirname(os.path.abspath(__file__)), name)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    retcode = p.wait()
    out = p.stdout.read()
    err = p.stderr.read()
    if len(err) > 0:
        fail(err)


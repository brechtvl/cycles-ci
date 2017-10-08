
import subprocess
import sys

class RunException(Exception):
    pass

# command utilities
def run(args, log=None, cwd=None, silent=False):
    if log:
        cmd = '$ ' + ' '.join(args) + '\n'
        sys.stdout.write(cmd)
        log.write(cmd)
    proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while proc.poll() is None:
        line = proc.stdout.readline()
        if line and not silent:
            if log:
                line = line.decode('utf-8', 'ignore')
                log.write(line)
                #sys.stdout.write(line)

    if proc.returncode != 0 and not silent:
        if log:
            log.flush()
        raise RunException("Error executing command")

def parse(args, cwd=None):
    proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate()
    return stdout.decode('utf-8', 'ignore').strip()


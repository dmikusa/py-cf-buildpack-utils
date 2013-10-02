import os
from subprocess import Popen
from subprocess import PIPE


class CloudFoundryRunner(object):
    @staticmethod
    def run_from_directory(folder, command, args, shell=False):
        if os.path.exists(folder):
            cwd = os.getcwd()
            try:
                os.chdir(folder)
                cmd = [command, ]
                cmd.extend(args)
                proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell)
                stdout, stderr = proc.communicate()
                retcode = proc.poll()
                return (retcode, stdout, stderr)
            finally:
                os.chdir(cwd)

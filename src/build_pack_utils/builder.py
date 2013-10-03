import os
from subprocess import Popen
from subprocess import PIPE
from cloudfoundry import CloudFoundryUtil
from cloudfoundry import CloudFoundryInstaller


class Runner(object):
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


class Builder(object):
    def __init__(self):
        # Do this first.  Sets up STDOUT and gives us access to basic info
        #  like build directory, cache directory, memory limit, temp dir,
        #  and build pack directory.  Also has utilities for loading JSON
        #  configuration files.
        self.cf = CloudFoundryUtil()

        # Just a place holder for our installer, gets initialized after
        #  a configuration is selected.
        self.installer = None

        # Just a place holder for our config, gets initialized when the
        #  user select a particular configuration to use
        self.cfg = None

    def use(self, cfg):
        self.cfg = cfg
        self.installer = CloudFoundryInstaller(self.cf, self.cfg)

    def default_config(self):
        return self.cf.load_json_config_file_from(
            self.cf.BP_DIR,
            self.cfg.get('DEFAULT_CONFIG_PATH', 'options.json'))

    def user_config(self):
        return self.cf.load_json_config_file_from(
            self.cf.BUILD_DIR,
            self.cfg.get('DEFAULT_USER_CONFIG_PATH', 'config.json'))

    def merge(self, *args):
        cfg = {}
        for arg in args:
            cfg.update(arg)
        return cfg

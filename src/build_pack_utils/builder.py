import os
from subprocess import Popen
from subprocess import PIPE
from cloudfoundry import CloudFoundryUtil
from cloudfoundry import CloudFoundryInstaller
# TODO: look at naming conventions used here
#        use _ to indicate internal state


class Configurer(object):
    def __init__(self, builder):
        self.builder = builder
        self.builder.cfg = {}

    def default_config(self):
        self._merge(
            self.builder.cf.load_json_config_file_from(
                self.builder.cf.BP_DIR,
                'defaults/options.json'))
        return self

    def user_config(self, path=None):
        if path is None:
            path = os.path.join('config', 'options.json')
        self._merge(
            self.builder.cf.load_json_config_file_from(
                self.builder.cf.BUILD_DIR, path))
        return self

    def done(self):
        self.builder.installer = \
            CloudFoundryInstaller(
                self.builder.cf,
                self.builder.cfg)
        return self.builder

    def _merge(self, cfg):
        self.builder.cfg.update(cfg)


class Installer(object):
    def __init__(self, builder):
        self.builder = builder

    def package(self, key):
        self.builder.cfg['%s_INSTALL_PATH' % key] = \
            self.builder.installer.install_binary(key)
        return self

    def packages(self, *keys):
        for key in keys:
            self.package(key)
        return self

    def done(self):
        return self.builder


class Runner(object):
    def __init__(self, builder):
        self.builder = builder
        self.path = os.getcwd()
        self.shell = False
        self.cmd = []
        self.on_finish_method = None
        self.on_success_method = None
        self.on_fail_method = None

    def done(self):
        if os.path.exists(self.path):
            cwd = os.getcwd()
            try:
                os.chdir(self.path)
                proc = Popen(self.cmd, stdout=PIPE,
                             stderr=PIPE, shell=self.shell)
                stdout, stderr = proc.communicate()
                retcode = proc.poll()
                if self.on_finish_method:
                    self.on_finish_method(self.cmd, retcode, stdout, stderr)
                else:
                    if retcode == 0 and self.on_success:
                        self.on_success_method(self.cmd, retcode, stdout)
                    else:
                        self.on_fail_method(self.cmd, retcode, stderr)
            finally:
                os.chdir(cwd)
        return self.builder

    def command(self, command, shell=True):
        if hasattr(command, '__call__'):
            self.cmd = command(self.builder.cfg)
        elif hasattr(command, 'split'):
            self.cmd = command.split(' ')
        else:
            self.cmd = command
        return self

    def out_of(self, path):
        if hasattr(path, '__call__'):
            self.path = path(self.builder.cfg)
        elif path in self.builder.cfg.keys():
            self.path = self.builder.cfg[path]
        else:
            self.path = path
        return self

    def with_shell(self):
        self.shell = True
        return self

    def on_success(self, on_success_method):
        if hasattr(on_success_method, '__call__'):
            self.on_success_method = on_success_method
        return self

    def on_fail(self, on_fail_method):
        if hasattr(on_fail_method, '__call__'):
            self.on_fail_method = on_fail_method
        return self

    def on_finish(self, on_finish_method):
        if hasattr(on_finish_method, '__call__'):
            self.on_finish_method = on_finish_method
        return self


class Executor(object):
    def __init__(self, builder):
        self.builder = builder

    def method(self, execute):
        if hasattr(execute, '__call__'):
            execute(self.builder.cfg)
        return self.builder


class StartScriptBuilder(object):
    def __init__(self, builder):
        self.builder = builder
        self.content = []

    def manual(self, cmd):
        self.content.append(cmd)

    def environment_variable(self):
        return EnvironmentVariableBuilder(self)

    def command(self):
        return ScriptCommandBuilder(self)

    def write(self):
        startScriptPath = os.path.join(
            self.builder.cf.BUILD_DIR, 'start.sh')
        with open(startScriptPath, 'wt') as out:
            out.write('\n'.join(self.content))
        os.chmod(startScriptPath, 0755)
        return self.builder


class ScriptCommandBuilder(object):
    def __init__(self, scriptBuilder):
        self.scriptBuilder = scriptBuilder
        self.command = None
        self.args = []
        self.bg = False
        self.redirect_stdout = None
        self.redirect_stderr = None
        self.redirect_both = None
        self.content = []

    def manual(self, cmd):
        self.content.append(cmd)
        return self

    def run(self, command):
        self.command = command
        return self

    def with_argument(self, argument):
        self.args.append(argument)
        return self

    def background(self):
        self.bg = True
        return self

    def redirect(self, stderr=None, stdout=None, both=None):
        self.redirect_stderr = stderr
        self.redirect_stdout = stdout
        self.redirect_both = both
        return self

    def pipe(self):
        # background should be on last command only
        self.bg = False
        return ScriptCommandBuilder(self)

    def done(self):
        cmd = []
        if self.command:
            cmd.append(self.command)
            cmd.extend(self.args)
            if self.redirect_both:
                cmd.append('&> %s' % self.redirect_both)
            elif self.redirect_stdout:
                cmd.append('> %s' % self.redirect_stdout)
            elif self.redirect_stderr:
                cmd.append('2> %s' % self.redirect_stderr)
            if self.bg:
                cmd.append('&')
        if self.content:
            if self.command:
                cmd.append('|')
            cmd.append(' '.join(self.content))
        self.scriptBuilder.manual(' '.join(cmd))
        return self.scriptBuilder


class EnvironmentVariableBuilder(object):
    def __init__(self, scriptBuilder):
        self.scriptBuilder = scriptBuilder
        self._name = None
        self._export = False

    def export(self):
        self._export = True
        return self

    def name(self, name):
        self._name = name
        return self

    def value(self, value):
        if not self._name:
            raise ValueError('You must specify a name')
        builder = self.scriptBuilder.builder
        if hasattr(value, '__call__'):
            value = value()
        elif value in builder.cfg.keys():
            value = builder.cfg[value]
        value = value.replace(builder.cf.BUILD_DIR, '$HOME')
        line = []
        if self._export:
            line.append('export')
        line.append("%s=%s" % (self._name, value))
        self.scriptBuilder.manual(' '.join(line))
        return self.scriptBuilder


class Builder(object):
    def __init__(self):
        self.cf = CloudFoundryUtil()
        self.installer = None
        self.cfg = None

    def configure(self):
        return Configurer(self)

    def install(self):
        return Installer(self)

    def run(self):
        return Runner(self)

    def execute(self):
        return Executor(self)

    def create_start_script(self):
        return StartScriptBuilder()

import os
from subprocess import Popen
from subprocess import PIPE
from cloudfoundry import CloudFoundryUtil
from cloudfoundry import CloudFoundryInstaller


class Configurer(object):
    def __init__(self, builder):
        self.builder = builder

    def default_config(self):
        self._merge(
            CloudFoundryUtil.load_json_config_file_from(
                self.builder._ctx['BP_DIR'],
                'defaults/options.json'))
        return self

    def user_config(self, path=None):
        if path is None:
            path = os.path.join('config', 'options.json')
        self._merge(
            CloudFoundryUtil.load_json_config_file_from(
                self.builder._ctx['BUILD_DIR'], path))
        return self

    def done(self):
        self.builder._installer = \
            CloudFoundryInstaller(self.builder._ctx)
        return self.builder

    def _merge(self, ctx):
        self.builder._ctx.update(ctx)


class Installer(object):
    def __init__(self, builder):
        self.builder = builder

    def package(self, key):
        self.builder._ctx['%s_INSTALL_PATH' % key] = \
            self.builder._installer.install_binary(key)
        return self

    def packages(self, *keys):
        for key in keys:
            self.package(key)
        return self

    def done(self):
        return self.builder


class Runner(object):
    def __init__(self, builder):
        self._builder = builder
        self._path = os.getcwd()
        self._shell = False
        self._cmd = []
        self._on_finish = None
        self._on_success = None
        self._on_fail = None

    def done(self):
        if os.path.exists(self._path):
            cwd = os.getcwd()
            try:
                os.chdir(self._path)
                proc = Popen(self._cmd, stdout=PIPE,
                             stderr=PIPE, shell=self._shell)
                stdout, stderr = proc.communicate()
                retcode = proc.poll()
                if self._on_finish:
                    self._on_finish(self._cmd, retcode, stdout, stderr)
                else:
                    if retcode == 0 and self._on_success:
                        self._on_success(self._cmd, retcode, stdout)
                    else:
                        self._on_fail(self._cmd, retcode, stderr)
            finally:
                os.chdir(cwd)
        return self._builder

    def command(self, command, shell=True):
        if hasattr(command, '__call__'):
            self._cmd = command(self._builder._ctx)
        elif hasattr(command, 'split'):
            self._cmd = command.split(' ')
        else:
            self._cmd = command
        return self

    def out_of(self, path):
        if hasattr(path, '__call__'):
            self._path = path(self._builder._ctx)
        elif path in self._builder._ctx.keys():
            self._path = self._builder._ctx[path]
        else:
            self._path = path
        return self

    def with_shell(self):
        self._shell = True
        return self

    def on_success(self, on_success):
        if hasattr(on_success, '__call__'):
            self._on_success = on_success
        return self

    def on_fail(self, on_fail):
        if hasattr(on_fail, '__call__'):
            self._on_fail = on_fail
        return self

    def on_finish(self, on_finish):
        if hasattr(on_finish, '__call__'):
            self._on_finish = on_finish
        return self


class Executor(object):
    def __init__(self, builder):
        self.builder = builder

    def method(self, execute):
        if hasattr(execute, '__call__'):
            execute(self.builder._ctx)
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
        scriptName = self.builder._ctx.get('START_SCRIPT_NAME',
                                          'start.sh')
        startScriptPath = os.path.join(
            self.builder._ctx['BUILD_DIR'], scriptName)
        with open(startScriptPath, 'wt') as out:
            out.write('\n'.join(self.content))
        os.chmod(startScriptPath, 0755)
        return self.builder


class ScriptCommandBuilder(object):
    def __init__(self, scriptBuilder):
        self._scriptBuilder = scriptBuilder
        self._command = None
        self._args = []
        self._background = False
        self._stdout = None
        self._stderr = None
        self._both = None
        self._content = []

    def manual(self, cmd):
        self._content.append(cmd)
        return self

    def run(self, command):
        self._command = command
        return self

    def with_argument(self, argument):
        self._args.append(argument)
        return self

    def background(self):
        self._background = True
        return self

    def redirect(self, stderr=None, stdout=None, both=None):
        self._stderr = stderr
        self._stdout = stdout
        self._both = both
        return self

    def pipe(self):
        # background should be on last command only
        self._background = False
        return ScriptCommandBuilder(self)

    def done(self):
        cmd = []
        if self._command:
            cmd.append(self._command)
            cmd.extend(self._args)
            if self._both:
                cmd.append('&> %s' % self._both)
            elif self._stdout:
                cmd.append('> %s' % self._stdout)
            elif self._stderr:
                cmd.append('2> %s' % self._stderr)
            if self._background:
                cmd.append('&')
        if self._content:
            if self._command:
                cmd.append('|')
            cmd.append(' '.join(self._content))
        self._scriptBuilder.manual(' '.join(cmd))
        return self._scriptBuilder


class EnvironmentVariableBuilder(object):
    def __init__(self, scriptBuilder):
        self._scriptBuilder = scriptBuilder
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
        builder = self._scriptBuilder.builder
        if hasattr(value, '__call__'):
            value = value()
        elif value in builder._ctx.keys():
            value = builder._ctx[value]
        value = value.replace(builder._ctx['BUILD_DIR'], '$HOME')
        line = []
        if self._export:
            line.append('export')
        line.append("%s=%s" % (self._name, value))
        self._scriptBuilder.manual(' '.join(line))
        return self._scriptBuilder


class Builder(object):
    def __init__(self):
        self._installer = None
        self._ctx = None

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

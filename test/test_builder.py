import os
import stat
import tempfile
from nose.tools import eq_
from nose.tools import raises
from nose.tools import with_setup
from dingus import Dingus
from build_pack_utils import Runner
from build_pack_utils import Configurer
from build_pack_utils import Installer
from build_pack_utils import Executor
from build_pack_utils import StartScriptBuilder
from build_pack_utils import ScriptCommandBuilder
from build_pack_utils import EnvironmentVariableBuilder


class TestConfigurer(object):
    def setUp(self):
        self.ctx = {
            'BUILD_DIR': './test/data',
            'BP_DIR': './test/data'
        }
        self.builder = Dingus(_ctx=self.ctx)
        self.cfgur = Configurer(self.builder)

    @with_setup(setup=setUp)
    def test_default_config(self):
        assert 2 == len(self.ctx.keys())
        res = self.cfgur.default_config()
        assert 6 == len(self.ctx.keys())
        assert 'BUILD_DIR' in self.ctx.keys()
        assert 'BP_DIR' in self.ctx.keys()
        assert 'list' in self.ctx.keys()
        assert 'string' in self.ctx.keys()
        assert 'int' in self.ctx.keys()
        assert 'map' in self.ctx.keys()
        assert res is self.cfgur

    @with_setup(setup=setUp)
    def test_user_config(self):
        res = self.cfgur.user_config()
        assert 6 == len(self.ctx.keys())
        assert 'BUILD_DIR' in self.ctx.keys()
        assert 'BP_DIR' in self.ctx.keys()
        assert 'list' in self.ctx.keys()
        assert 'string' in self.ctx.keys()
        assert 'int' in self.ctx.keys()
        assert 'map' in self.ctx.keys()
        assert res is self.cfgur


class TestInstaller(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': '/tmp/build_dir',
            'CACHE_DIR': '/tmp/cache',
            'BP_DIR': '/tmp/build_dir'
        }
        self.builder = Dingus(_ctx=self.ctx)
        self.inst = Installer(self.builder)

    def test_package(self):
        self.inst._installer = Dingus(
            install_binary__returns='/tmp/installed/TEST') 
        res = self.inst.package('TEST')
        assert 'TEST_INSTALL_PATH' in self.ctx
        eq_('/tmp/installed/TEST', self.ctx['TEST_INSTALL_PATH'])
        assert self.inst == res

    def test_packages(self):
        self.inst._installer = Dingus()
        self.inst._installer.install_binary = lambda x: '/tmp/installed/%s' % x
        res = self.inst.packages('TEST1', 'TEST2')
        assert 'TEST1_INSTALL_PATH' in self.ctx
        eq_('/tmp/installed/TEST1', self.ctx['TEST1_INSTALL_PATH'])
        assert 'TEST2_INSTALL_PATH' in self.ctx
        eq_('/tmp/installed/TEST2', self.ctx['TEST2_INSTALL_PATH'])
        assert self.inst == res

    def test_done(self):
        res = self.inst.done()
        assert self.builder == res


class TestExecutor(object):
    def test_method(self):
        method = Dingus()
        builder = Dingus()
        ex = Executor(builder)
        res = ex.method(method)
        assert res is builder
        assert method.calls().once()


class TestRunner(object):
    def __init__(self):
        self.builder = Dingus(cfg={'KEY': 'TEST'})

    def test_command_string(self):
        r = Runner(self.builder)
        res = r.command('TEST')
        assert res is r
        assert ['TEST'] == r._cmd

    def test_command_method(self):
        method = Dingus(return_value=['TEST'])
        r = Runner(self.builder)
        res = r.command(method)
        assert res is r
        assert ['TEST'] == r._cmd
        assert method.calls().once()

    def test_command_list(self):
        r = Runner(self.builder)
        res = r.command(['TEST'])
        assert res is r
        assert ['TEST'] == r._cmd

    def test_out_of_string(self):
        r = Runner(self.builder)
        res = r.out_of('TEST')
        assert res is r
        assert 'TEST' == r._path

    def test_out_of_method(self):
        method = Dingus(return_value='TEST')
        r = Runner(self.builder)
        res = r.out_of(method)
        assert res is r
        assert 'TEST' == r._path

    def test_out_of_key(self):
        r = Runner(self.builder)
        res = r.out_of('KEY')
        assert res is r
        eq_('KEY', r._path)

    def test_with_shell(self):
        r = Runner(self.builder)
        assert not r._shell
        res = r.with_shell()
        assert res is r
        assert r._shell

    def test_on_success(self):
        method = Dingus()
        r = Runner(self.builder)
        assert r._on_success is None
        res = r.on_success(method)
        assert res is r
        assert method is r._on_success
        assert 0 == len(method.calls())

    def test_on_fail(self):
        method = Dingus()
        r = Runner(self.builder)
        assert r._on_fail is None
        res = r.on_fail(method)
        assert res is r
        assert method is r._on_fail
        assert 0 == len(method.calls())

    def test_on_finish(self):
        method = Dingus()
        r = Runner(self.builder)
        assert r._on_finish is None
        res = r.on_finish(method)
        assert res is r
        assert method is r._on_finish
        assert 0 == len(method.calls())

    def test_environment_variable(self):
        r = Runner(self.builder)
        preLen = len(r._env.keys())
        res = (r.environment_variable()
                   .name('JUNK')
                   .value('2134'))
        assert r is res
        assert 1 == (len(r._env.keys()) - preLen)
        assert 'JUNK' in r._env.keys()
        eq_('2134', r._env['JUNK'])

    def test_done(self):
        on_success = Dingus()
        r = Runner(self.builder)
        r.command('ls -la')
        r.out_of('./test/data')
        r.on_success(on_success)
        res = r.done()
        assert res is self.builder
        assert on_success.calls().once()
        assert 3 == len(on_success.calls()[0].args)
        cmd = on_success.calls()[0].args[0]
        assert 2 == len(cmd)
        assert 'ls' == cmd[0]
        assert '-la' == cmd[1]
        assert 0 == on_success.calls()[0].args[1]
        assert on_success.calls()[0].args[2].find('HASH.tar.bz2') >= 0

    def test_done_fail(self):
        on_fail = Dingus()
        r = Runner(self.builder)
        r.command('ls -la /does/not/exist')
        r.on_fail(on_fail)
        res = r.done()
        assert res is self.builder
        assert on_fail.calls().once()
        assert 3 == len(on_fail.calls()[0].args)
        cmd = on_fail.calls()[0].args[0]
        assert 3 == len(cmd)
        assert 'ls' == cmd[0]
        assert '-la' == cmd[1]
        assert '/does/not/exist' == cmd[2]
        assert 1 == on_fail.calls()[0].args[1]
        assert on_fail.calls()[0].args[2].find(
            'No such file or directory') >= 0

    def test_done_finish(self):
        on_finish = Dingus()
        r = Runner(self.builder)
        r.command('ls -la /does/not/exist')
        r.on_finish(on_finish)
        res = r.done()
        assert res is self.builder
        assert on_finish.calls().once()
        assert 4 == len(on_finish.calls()[0].args)
        cmd = on_finish.calls()[0].args[0]
        assert 3 == len(cmd)
        assert 'ls' == cmd[0]
        assert '-la' == cmd[1]
        assert '/does/not/exist' == cmd[2]
        assert 1 == on_finish.calls()[0].args[1]
        assert '' == on_finish.calls()[0].args[2]
        assert on_finish.calls()[0].args[3].find(
            'No such file or directory') >= 0

    def test_done_env(self):
        on_finish = Dingus()
        r = Runner(self.builder)
        r.on_finish(on_finish)
        r.command('env')
        r.environment_variable().name('HELLO').value('Hello World!')
        res = r.done()
        assert res is self.builder
        assert on_finish.calls().once()
        assert on_finish.calls()[0].args[2].find('HELLO=Hello World!') > -1

    def test_done_args_with_shell(self):
        on_finish = Dingus()
        r = Runner(self.builder)
        r.on_finish(on_finish)
        r.command('ls -la /tmp')
        r.with_shell()
        res = r.done()
        assert res is self.builder
        assert on_finish.calls().once()
        assert (on_finish.calls()[0].args[2].find('hsperfdata_cloud') > -1 or
                on_finish.calls()[0].args[2].find('private') > -1)


class TestStartScriptBuilder(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': tempfile.gettempdir(),
            'BP_DIR': '/tmp/build_dir'
        }
        self.builder = Dingus(_ctx=self.ctx)

    def test_write(self):
        b = StartScriptBuilder(self.builder)
        b.manual('ls -la')
        b.manual('echo Hello World')
        b.manual('X=1234')
        expectedFile = None
        try:
            b.write()
            expectedFile = os.path.join(tempfile.gettempdir(),
                                        'start.sh')
            assert os.path.exists(expectedFile)
            eq_('0755', oct(stat.S_IMODE(os.lstat(expectedFile).st_mode)))
            data = open(expectedFile, 'rt').read()
            assert data.find('ls -la') >= 0
            assert data.find('echo') >= 0
            assert data.find('1234') >= 0
        finally:
            if expectedFile and os.path.exists(expectedFile):
                os.remove(expectedFile)

    def test_fancy_1(self):
        ssb = (StartScriptBuilder(self.builder)
                   .environment_variable()
                       .export()
                       .name('TEST')
                       .value('1234')
                   .environment_variable()
                       .name('JUNK')
                       .value('4321')
                   .command()
                       .manual('ls -lath')
                       .done()
                   .command()
                       .run('ps')
                       .with_argument('aux')
                       .pipe()
                           .run('grep')
                           .with_argument('catalina')
                           .done()
                       .done()
                   .command()
                       .run('start.sh')
                       .background()
                       .done())
        assert hasattr(ssb, 'write')
        eq_('export TEST=1234', ssb.content[0])
        eq_('JUNK=4321', ssb.content[1])
        eq_('ls -lath', ssb.content[2])
        eq_('ps aux | grep catalina', ssb.content[3])
        eq_('start.sh &', ssb.content[4])


class TestScriptCommandBuilder(object):
    def __init__(self):
        self.ssb = Dingus()

    def test_manual(self):
        scb = ScriptCommandBuilder(self.ssb)
        res = scb.manual('ls -la')
        assert res is scb
        assert len(scb._content) == 1
        assert 'ls -la' == scb._content[0]

    def test_run(self):
        scb = ScriptCommandBuilder(self.ssb)
        res = scb.run('ls')
        assert res is scb
        assert 'ls' == scb._command

    def test_with_argument(self):
        scb = ScriptCommandBuilder(self.ssb)
        res = scb.with_argument('-la')
        assert res is scb
        assert 1 == len(scb._args)
        assert '-la' == scb._args[0]

    def test_background(self):
        scb = ScriptCommandBuilder(self.ssb)
        assert not scb._background
        res = scb.background()
        assert res is scb
        assert scb._background

    def test_redirect(self):
        scb = ScriptCommandBuilder(self.ssb)
        res = scb.redirect(stderr=1, stdout=2, both=3)
        assert res is scb
        assert 1 == scb._stderr
        assert 2 == scb._stdout
        assert 3 == scb._both

    def test_pipe(self):
        scb = ScriptCommandBuilder(self.ssb)
        scb.background()
        assert scb._background
        res = scb.pipe()
        assert res is not scb
        assert not scb._background

    def test_done_simple(self):
        scb = ScriptCommandBuilder(self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.with_argument('/some/path')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la /some/path' == self.ssb.calls()[0].args[0]

    def test_done_redirect_stderr(self):
        scb = ScriptCommandBuilder(self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.redirect(stderr='/dev/null')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la 2> /dev/null' == self.ssb.calls()[0].args[0]

    def test_done_redirect_stdout(self):
        scb = ScriptCommandBuilder(self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.redirect(stdout='/dev/null')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la > /dev/null' == self.ssb.calls()[0].args[0]

    def test_done_redirect_both(self):
        scb = ScriptCommandBuilder(self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.redirect(both='/dev/null')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la &> /dev/null' == self.ssb.calls()[0].args[0]

    def test_done_background(self):
        scb = ScriptCommandBuilder(self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.background()
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la &' == self.ssb.calls()[0].args[0]

    def test_done_pipe(self):
        scb = ScriptCommandBuilder(self.ssb)
        scb.run('ps')
        scb.with_argument('aux')
        subCmd = scb.pipe()
        subCmd.run('grep')
        subCmd.with_argument('catalina')
        subCmd.done()
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        eq_('ps aux | grep catalina', self.ssb.calls()[0].args[0])

    def test_done_fancy(self):
        res = (ScriptCommandBuilder(self.ssb)
                   .run('ps')
                   .with_argument('aux')
                   .pipe()
                       .run('grep')
                       .with_argument('catalina')
                       .background()
                       .done()
                   .done())
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        eq_('ps aux | grep catalina &', self.ssb.calls()[0].args[0])


class TestEnvironmentVariableBuilder(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': '/tmp/build_dir',
            'BP_DIR': '/tmp/bp_dir',
            'VAL': '1234'
        }
        self.builder = Dingus(_ctx=self.ctx)
        self.ssb = Dingus(builder=self.builder)

    def test_export(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        assert not evb._export
        res = evb.export()
        assert res is evb
        assert evb._export

    def test_name(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        res = evb.name('TEST')
        assert res is evb
        assert 'TEST' == evb._name

    @raises(ValueError)
    def test_value_no_name(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        evb.value('1234')

    def test_value_method(self):
        method = Dingus(return_value='1234')
        evb = EnvironmentVariableBuilder(self.ssb)
        evb.name('TEST')
        res = evb.value(method)
        assert res is self.ssb
        assert method.calls().once()
        assert 0 == len(method.calls()[0].args)
        eq_('TEST=1234', self.ssb.calls()[0].args[0])

    def test_value_string(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        evb.name('TEST')
        res = evb.value('1234')
        assert res is self.ssb
        eq_('TEST=1234', self.ssb.calls()[0].args[0])

    def test_value_config(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        evb.name('TEST')
        res = evb.value('VAL')
        assert res is self.ssb
        eq_('TEST=1234', self.ssb.calls()[0].args[0])

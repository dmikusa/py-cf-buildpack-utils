import os
import sys
import stat
import tempfile
import shutil
from StringIO import StringIO
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
from build_pack_utils import Detecter
from build_pack_utils import Builder
from build_pack_utils import ConfigInstaller
from build_pack_utils import FileUtil


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


class TestDetector(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': '/tmp/build_dir'
        }
        self.builder = Dingus(_ctx=self.ctx)

    def test_with_regex(self):
        d = Detecter(self.builder)
        res = d.with_regex('^.*\.php$')
        assert res is d
        assert d._detecter._match('index.php')

    def test_by_name(self):
        d = Detecter(self.builder)
        res = d.by_name('index.php')
        assert res is d
        assert d._detecter._match('index.php')

    def test_starts_with(self):
        d = Detecter(self.builder)
        res = d.starts_with('index')
        assert res is d
        assert d._detecter._match('index.php')

    def test_ends_with(self):
        d = Detecter(self.builder)
        res = d.ends_with('.php')
        assert res is d
        assert d._detecter._match('index.php')

    def test_contains(self):
        d = Detecter(self.builder)
        res = d.contains('dex')
        assert res is d
        assert d._detecter._match('index.php')

    def test_recursive(self):
        d = Detecter(self.builder)
        d.by_name('index.php')
        res = d.recursive()
        assert res is d
        assert d._recursive
        assert d._detecter.recursive

    def test_using_full_path(self):
        d = Detecter(self.builder)
        d.by_name('index.php')
        res = d.using_full_path()
        assert res is d
        assert d._fullPath
        assert d._detecter.fullPath

    def test_if_found_output(self):
        d = Detecter(self.builder)
        res = d.if_found_output('TEST')
        assert res is d
        eq_('TEST', d._output)

    def test_under(self):
        d = Detecter(self.builder)
        res = d.under('TEST')
        assert res is d
        eq_('TEST', d._root)
        assert d._recursive

    def test_at(self):
        d = Detecter(self.builder)
        res = d.at('TEST')
        assert res is d
        eq_('TEST', d._root)
        assert not d._recursive

    def test_done_found(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            d = Detecter(self.builder)
            d.at('./test/data')
            d.by_name('HASH')
            d.if_found_output('HASH')
            d.done()
            assert False  # shouldFail
        except SystemExit, e:
            eq_(0, e.code)
        finally:
            sys.stdout = old_sysout
        eq_('HASH\n', new_sysout.getvalue())

    def test_done_not_found(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            d = Detecter(self.builder)
            d.at('./test/data')
            d.by_name('NOTFOUND')
            d.if_found_output('HASH')
            d.done()
            assert False  # shouldFail
        except SystemExit, e:
            eq_(1, e.code)
        finally:
            sys.stdout = old_sysout
        eq_('no\n', new_sysout.getvalue())


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


class TestConfigInstaller(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': 'test/data/',
            'CACHE_DIR': '/tmp/cache',
            'BP_DIR': 'test/data/'
        }
        self.cfInst = Dingus()
        self.builder = Dingus(_ctx=self.ctx)
        self.inst = Installer(self.builder)
        self.inst._installer = self.cfInst
        self.cfgInst = ConfigInstaller(self.inst)

    def test_from_build_pack(self):
        res = self.cfgInst.from_build_pack('some/file.txt')
        assert res is self.cfgInst
        eq_('some/file.txt', self.cfgInst._bp_path)

    def test_or_from_build_pack(self):
        res = self.cfgInst.or_from_build_pack('some/file.txt')
        assert res is self.cfgInst
        eq_('some/file.txt', self.cfgInst._bp_path)

    def test_from_application(self):
        res = self.cfgInst.from_application('some/file.txt')
        assert res is self.cfgInst
        eq_('some/file.txt', self.cfgInst._app_path)

    def test_to(self):
        res = self.cfgInst.to('some/other/file.txt')
        assert res is self.cfgInst
        eq_('some/other/file.txt', self.cfgInst._to_path)

    def test_all_files(self):
        assert not self.cfgInst._all_files
        res = self.cfgInst.all_files()
        assert res is self.cfgInst
        assert self.cfgInst._all_files

    def test_done_nothing(self):
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(0, len(self.cfInst.calls()))
        self.cfgInst.to('some/path')
        self.cfgInst.done()
        eq_(0, len(self.cfInst.calls()))
        self.cfgInst._to_path = None
        self.cfgInst.from_build_pack('some/path')
        eq_(0, len(self.cfInst.calls()))
        self.cfgInst.from_application('some/path')
        eq_(0, len(self.cfInst.calls()))

    def test_done_single_bp(self):
        self.cfgInst.from_build_pack('some/file.txt')
        self.cfgInst.to('some/other/file.txt')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_('install_from_build_pack', self.cfInst.calls()[0].name)
        assert 2 == len(self.cfInst.calls()[0].args)
        eq_('some/file.txt', self.cfInst.calls()[0].args[0])
        eq_('some/other/file.txt', self.cfInst.calls()[0].args[1])

    def test_done_single_app(self):
        self.cfgInst.from_application('some/file.txt')
        self.cfgInst.to('some/other/file.txt')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_('install_from_application', self.cfInst.calls()[0].name)
        assert 2 == len(self.cfInst.calls()[0].args)
        eq_('some/file.txt', self.cfInst.calls()[0].args[0])
        eq_('some/other/file.txt', self.cfInst.calls()[0].args[1])

    def test_done_single_bp_then_app(self):
        self.cfgInst.from_application('some/file.txt')
        self.cfgInst.or_from_build_pack('default/file.txt')
        self.cfgInst.to('some/other/file.txt')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(2, len(self.cfInst.calls()))
        eq_('install_from_build_pack', self.cfInst.calls()[0].name)
        eq_('install_from_application', self.cfInst.calls()[1].name)
        assert 2 == len(self.cfInst.calls()[0].args)
        eq_('default/file.txt', self.cfInst.calls()[0].args[0])
        eq_('some/other/file.txt', self.cfInst.calls()[0].args[1])
        assert 2 == len(self.cfInst.calls()[1].args)
        eq_('some/file.txt', self.cfInst.calls()[1].args[0])
        eq_('some/other/file.txt', self.cfInst.calls()[1].args[1])

    def test_done_multi_bp(self):
        self.cfgInst.all_files()
        self.cfgInst.from_build_pack('defaults')
        self.cfgInst.to('some/folder')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(2, len(self.cfInst.calls('install_from_build_pack')))
        call = self.cfInst.calls('install_from_build_pack')[1]
        eq_(2, len(call.args))
        eq_('defaults/options.json', call.args[0])
        eq_('some/folder/options.json', call.args[1])
        call = self.cfInst.calls('install_from_build_pack')[0]
        eq_(2, len(call.args))
        eq_('defaults/junk.xml', call.args[0])
        eq_('some/folder/junk.xml', call.args[1])

    def test_done_multi_app(self):
        self.cfgInst.all_files()
        self.cfgInst.from_application('config')
        self.cfgInst.to('some/folder')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(2, len(self.cfInst.calls('install_from_application')))
        call = self.cfInst.calls('install_from_application')[1]
        eq_(2, len(call.args))
        eq_('config/options.json', call.args[0])
        eq_('some/folder/options.json', call.args[1])
        call = self.cfInst.calls('install_from_application')[0]
        eq_(2, len(call.args))
        eq_('config/junk.xml', call.args[0])
        eq_('some/folder/junk.xml', call.args[1])

    def test_done_multi_bp_then_app(self):
        self.cfgInst.all_files()
        self.cfgInst.from_application('config')
        self.cfgInst.or_from_build_pack('defaults')
        self.cfgInst.to('some/folder')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(2, len(self.cfInst.calls('install_from_build_pack')))
        call = self.cfInst.calls('install_from_build_pack')[1]
        eq_(2, len(call.args))
        eq_('defaults/options.json', call.args[0])
        eq_('some/folder/options.json', call.args[1])
        call = self.cfInst.calls('install_from_build_pack')[0]
        eq_(2, len(call.args))
        eq_('defaults/junk.xml', call.args[0])
        eq_('some/folder/junk.xml', call.args[1])
        eq_(2, len(self.cfInst.calls('install_from_application')))
        call = self.cfInst.calls('install_from_application')[1]
        eq_(2, len(call.args))
        eq_('config/options.json', call.args[0])
        eq_('some/folder/options.json', call.args[1])
        call = self.cfInst.calls('install_from_application')[0]
        eq_(2, len(call.args))
        eq_('config/junk.xml', call.args[0])
        eq_('some/folder/junk.xml', call.args[1])


class TestExecutor(object):
    def test_method(self):
        method = Dingus()
        builder = Dingus()
        ex = Executor(builder)
        res = ex.method(method)
        assert res is builder
        assert method.calls().once()


class TestFileUtil(object):
    def __init__(self):
        self.builder = Dingus(_ctx={'BUILD_DIR': '/tmp/build_dir'})

    def test_everything(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.everything()
        eq_(1, len(fu._filters))
        assert fu._filters[0]('always true')

    def test_all_files(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.all_files()
        eq_(1, len(fu._filters))
        assert fu._filters[0]('./test/data/HASH')
        assert not fu._filters[0]('./test/data/config')

    def test_hidden(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.hidden()
        eq_(1, len(fu._filters))
        assert fu._filters[0]('.test')
        assert not fu._filters[0]('config')

    def test_not_hidden(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.not_hidden()
        eq_(1, len(fu._filters))
        assert not fu._filters[0]('.test')
        assert fu._filters[0]('config')

    def test_all_folders(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.all_folders()
        eq_(1, len(fu._filters))
        assert not fu._filters[0]('./test/data/HASH')
        assert fu._filters[0]('./test/data/config')

    def test_where_name_matches(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.where_name_matches('.*\.gz')
        eq_(1, len(fu._filters))
        assert fu._filters[0]('./test/data/HASH.gz')
        assert not fu._filters[0]('./test/data/HASH.zip')

    def test_under(self):
        fu = FileUtil(self.builder)
        fu.under('./test/data')
        assert fu._from_path == './test/data'

    def test_into(self):
        fu = FileUtil(self.builder)
        fu.into('BUILD_DIR')
        eq_('/tmp/build_dir', fu._into_path)
        fu.under('./test/data')
        fu.into('new')
        eq_('./test/data/new', fu._into_path)
        fu.into('/tmp/test')
        eq_('/tmp/test', fu._into_path)

    def test_done_src_and_dest_match(self):
        fu = FileUtil(self.builder)
        fu.under('/tmp/data')
        fu.into('/tmp/data')
        try:
            fu.done()
            assert False
        except ValueError, e:
            eq_('Source and destination paths are the same [/tmp/data]',
                e.args[0])

    def test_done_src_does_not_exist(self):
        fu = FileUtil(self.builder)
        fu.under('/tmp/data')
        fu.into('/tmp/new')
        try:
            fu.done()
            assert False
        except ValueError, e:
            eq_('Source path [/tmp/data] does not exist',
                e.args[0])

    def test_done_dst_already_exists(self):
        fu = FileUtil(self.builder)
        fu.under('./test/data')
        fu.into('/tmp')
        try:
            fu.done()
            assert False
        except ValueError, e:
            eq_('Destination path [/tmp] already exists',
                e.args[0])

    def test_done_works_copy(self):
        tmp = os.path.join(tempfile.gettempdir(), 'test_done_works')
        try:
            fu = FileUtil(self.builder)
            fu.under('./test/data')
            fu.into(tmp)
            fu.done()
            eq_(15, len(os.listdir(tmp)))
            assert os.path.exists(tmp + '/config')
            assert os.path.isdir(tmp + '/config')
            eq_(2, len(os.listdir(tmp + '/config')))
        finally:
            shutil.rmtree(tmp)

    def test_done_works_move(self):
        tmp1 = os.path.join(tempfile.gettempdir(), 'test_done_works_1')
        tmp2 = os.path.join(tempfile.gettempdir(), 'test_done_works_2')
        try:
            shutil.copytree('./test/data', tmp1)
            eq_(15, len(os.listdir(tmp1)))
            fu = FileUtil(self.builder, move=True)
            fu.under(tmp1)
            fu.into(tmp2)
            fu.done()
            eq_(0, len(os.listdir(tmp1)))
            eq_(15, len(os.listdir(tmp2)))
            assert os.path.exists(tmp2 + '/config')
            assert os.path.isdir(tmp2 + '/config')
            eq_(2, len(os.listdir(tmp2 + '/config')))
        finally:
            shutil.rmtree(tmp1)
            shutil.rmtree(tmp2)


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
        self.builder = Dingus()
        self.ssb = Dingus()

    def test_manual(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        res = scb.manual('ls -la')
        assert res is scb
        assert len(scb._content) == 1
        assert 'ls -la' == scb._content[0]

    def test_run(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        res = scb.run('ls')
        assert res is scb
        assert 'ls' == scb._command

    def test_with_argument(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        res = scb.with_argument('-la')
        assert res is scb
        assert 1 == len(scb._args)
        assert '-la' == scb._args[0]

    def test_background(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        assert not scb._background
        res = scb.background()
        assert res is scb
        assert scb._background

    def test_redirect(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        res = scb.redirect(stderr=1, stdout=2, both=3)
        assert res is scb
        assert 1 == scb._stderr
        assert 2 == scb._stdout
        assert 3 == scb._both

    def test_pipe(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        scb.background()
        assert scb._background
        res = scb.pipe()
        assert res is not scb
        assert not scb._background

    def test_done_simple(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.with_argument('/some/path')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la /some/path' == self.ssb.calls()[0].args[0]

    def test_done_redirect_stderr(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.redirect(stderr='/dev/null')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la 2> /dev/null' == self.ssb.calls()[0].args[0]

    def test_done_redirect_stdout(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.redirect(stdout='/dev/null')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la > /dev/null' == self.ssb.calls()[0].args[0]

    def test_done_redirect_both(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.redirect(both='/dev/null')
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la &> /dev/null' == self.ssb.calls()[0].args[0]

    def test_done_background(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
        scb.run('ls')
        scb.with_argument('-la')
        scb.background()
        res = scb.done()
        assert res is self.ssb
        assert self.ssb.manual.calls().once()
        assert 'ls -la &' == self.ssb.calls()[0].args[0]

    def test_done_pipe(self):
        scb = ScriptCommandBuilder(self.builder, self.ssb)
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
        res = (ScriptCommandBuilder(self.builder, self.ssb)
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


class TestBuilder(object):
    def test_release(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            b = Builder()
            b.configure()
            b.release()
        finally:
            sys.stdout = old_sysout
        lines = new_sysout.getvalue().split('\n')
        assert 3 == len(lines)
        eq_('default_process_types:', lines[0])
        eq_('  web: $HOME/start.sh', lines[1])

    def test_release_custom_script(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            b = Builder()
            b.configure()
            b._ctx['START_SCRIPT_NAME'] = '$HOME/my-start-script.sh'
            b.release()
        finally:
            sys.stdout = old_sysout
        lines = new_sysout.getvalue().split('\n')
        assert 3 == len(lines)
        eq_('default_process_types:', lines[0])
        eq_('  web: $HOME/my-start-script.sh', lines[1])
        eq_('', lines[2])

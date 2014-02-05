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
from build_pack_utils import BuildPackManager
from build_pack_utils import ExtensionInstaller
from build_pack_utils import ModuleInstaller
from build_pack_utils import SaveBuilder
from build_pack_utils import utils


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


class TestDetecter(object):
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

    def test_continue(self):
        d = Detecter(self.builder)
        eq_(False, d._continue)
        res = d.when_not_found_continue()
        eq_(d, res)
        eq_(True, d._continue)

    def test_no_detecter(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            d = Detecter(self.builder)
            d.done()
            assert False  # shouldFail
        except SystemExit, e:
            eq_(1, e.code)
        finally:
            sys.stdout = old_sysout
        eq_('no\n', new_sysout.getvalue())

    def test_no_detecter_continue(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            d = Detecter(self.builder)
            d.when_not_found_continue()
            d.done()
        except SystemExit:
            assert False  # shouldFail
        finally:
            sys.stdout = old_sysout
        eq_('', new_sysout.getvalue())

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

    def test_done_continue(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            d = Detecter(self.builder)
            d.at('./test/data')
            d.by_name('NOTFOUND')
            d.if_found_output('HASH')
            d.when_not_found_continue()
            d.done()
        except SystemExit:
            assert False  # shouldFail
        finally:
            sys.stdout = old_sysout
        eq_('', new_sysout.getvalue())


class TestInstaller(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': '/tmp/build_dir',
            'CACHE_DIR': '/tmp/cache',
            'BP_DIR': '/tmp/build_dir',
            'PACKAGE': 'TMP'
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

    def test_package_from_ctx(self):
        self.inst._installer = Dingus(
            install_binary__returns='/tmp/installed/TMP')
        res = self.inst.package('PACKAGE')  # from ctx
        assert 'TMP_INSTALL_PATH' in self.ctx
        eq_('/tmp/installed/TMP', self.ctx['TMP_INSTALL_PATH'])
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
        self.ctx = utils.FormattedDict({
            'BUILD_DIR': 'test/data/',
            'CACHE_DIR': '/tmp/cache',
            'BP_DIR': 'test/data/',
            'VERSION': '1.0.0',
            'HOME': '/home/user',
            'TMPDIR': '/tmp',
            'SOMEPATH': '{TMPDIR}/path'
        })
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

    def test_format(self):
        res = self.cfgInst.to('test/{VERSION}')
        eq_(self.cfgInst, res)
        eq_('test/1.0.0', self.cfgInst._to_path)
        res = self.cfgInst.from_application('some/{VERSION}')
        eq_(self.cfgInst, res)
        eq_('some/1.0.0', self.cfgInst._app_path)
        res = self.cfgInst.from_build_pack('some/{VERSION}')
        eq_(self.cfgInst, res)
        eq_('some/1.0.0', self.cfgInst._bp_path)

    def test_rewrite(self):
        eq_(None, self.cfgInst._delimiter)
        res = self.cfgInst.rewrite()
        eq_(self.cfgInst, res)
        eq_('#', self.cfgInst._delimiter)
        res = self.cfgInst.rewrite(delimiter='@')
        eq_(self.cfgInst, res)
        eq_('@', self.cfgInst._delimiter)

    def assert_cfg_std(self, path):
        lines = open(path).readlines()
        eq_(8, len(lines))
        eq_('/home/user/test.cfg\n', lines[0])
        eq_('@{TMPDIR}/some-file.txt\n', lines[1])
        eq_('${TMPDIR}\n', lines[2])
        eq_('#{DNE}/test.txt\n', lines[3])
        eq_('@{DNE}/test.txt\n', lines[4])
        eq_('${DNE}/test.txt\n', lines[5])
        eq_('/tmp/path\n', lines[6])
        eq_('@{SOMEPATH}\n', lines[7])

    def test_rewrite_cfgs_compile(self):
        cfgPath = os.path.join(tempfile.gettempdir(), 'conf')
        cfgFile = os.path.join(tempfile.gettempdir(), 'conf', 'test.cfg')
        nestedPath = os.path.join(cfgPath, 'more')
        nestedFile = os.path.join(nestedPath, 'text.cfg')
        try:
            os.makedirs(nestedPath)
            shutil.copy('test/data/test.cfg', cfgFile)
            shutil.copy('test/data/test.cfg', nestedFile)
            self.cfgInst.to(cfgPath)
            self.cfgInst.rewrite()
            self.cfgInst._rewrite_cfgs()
            self.assert_cfg_std(cfgFile)
            self.assert_cfg_std(nestedFile)
        finally:
            shutil.rmtree(cfgPath)

    def test_rewrite_cfgs_delimiter(self):
        cfgPath = os.path.join(tempfile.gettempdir(), 'conf')
        cfgFile = os.path.join(tempfile.gettempdir(), 'conf', 'test.cfg')
        try:
            os.makedirs(cfgPath)
            shutil.copy('test/data/test.cfg', cfgFile)
            self.cfgInst.to(cfgPath)
            self.cfgInst.rewrite(delimiter='@')
            self.cfgInst._rewrite_cfgs()
            lines = open(cfgFile).readlines()
            eq_(8, len(lines))
            eq_('#{HOME}/test.cfg\n', lines[0])
            eq_('/tmp/some-file.txt\n', lines[1])
            eq_('${TMPDIR}\n', lines[2])
            eq_('#{DNE}/test.txt\n', lines[3])
            eq_('@{DNE}/test.txt\n', lines[4])
            eq_('${DNE}/test.txt\n', lines[5])
            eq_('#{SOMEPATH}\n', lines[6])
            eq_('/tmp/path\n', lines[7])
        finally:
            shutil.rmtree(cfgPath)

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

    def test_done_single_bp_rewrite(self):
        self.cfgInst._rewrite_cfgs = Dingus()
        self.cfgInst.from_build_pack('some/file.txt')
        self.cfgInst.to('some/other/file.txt')
        self.cfgInst.rewrite()
        res = self.cfgInst.done()
        assert res is self.inst
        eq_('install_from_build_pack', self.cfInst.calls()[0].name)
        eq_(2, len(self.cfInst.calls()[0].args))
        eq_('some/file.txt', self.cfInst.calls()[0].args[0])
        eq_('some/other/file.txt', self.cfInst.calls()[0].args[1])
        eq_(1, len(self.cfgInst._rewrite_cfgs.calls()))

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
        self.cfgInst.from_build_pack('defaults')
        self.cfgInst.to('some/folder')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(1, len(self.cfInst.calls('install_from_build_pack')))
        call = self.cfInst.calls('install_from_build_pack')[0]
        eq_(2, len(call.args))
        eq_('defaults', call.args[0])
        eq_('some/folder', call.args[1])
        call = self.cfInst.calls('install_from_build_pack')[0]
        eq_(2, len(call.args))
        eq_('defaults', call.args[0])
        eq_('some/folder', call.args[1])

    def test_done_multi_app(self):
        self.cfgInst.from_application('config')
        self.cfgInst.to('some/folder')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(1, len(self.cfInst.calls('install_from_application')))
        call = self.cfInst.calls('install_from_application')[0]
        eq_(2, len(call.args))
        eq_('config', call.args[0])
        eq_('some/folder', call.args[1])
        call = self.cfInst.calls('install_from_application')[0]
        eq_(2, len(call.args))
        eq_('config', call.args[0])
        eq_('some/folder', call.args[1])

    def test_done_multi_bp_then_app(self):
        self.cfgInst.from_application('config')
        self.cfgInst.or_from_build_pack('defaults')
        self.cfgInst.to('some/folder')
        res = self.cfgInst.done()
        assert res is self.inst
        eq_(1, len(self.cfInst.calls('install_from_build_pack')))
        call = self.cfInst.calls('install_from_build_pack')[0]
        eq_(2, len(call.args))
        eq_('defaults', call.args[0])
        eq_('some/folder', call.args[1])
        call = self.cfInst.calls('install_from_build_pack')[0]
        eq_(2, len(call.args))
        eq_('defaults', call.args[0])
        eq_('some/folder', call.args[1])
        eq_(1, len(self.cfInst.calls('install_from_application')))
        call = self.cfInst.calls('install_from_application')[0]
        eq_(2, len(call.args))
        eq_('config', call.args[0])
        eq_('some/folder', call.args[1])
        call = self.cfInst.calls('install_from_application')[0]
        eq_(2, len(call.args))
        eq_('config', call.args[0])
        eq_('some/folder', call.args[1])


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

    def test_where_name_does_not_match(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.where_name_does_not_match('.*\.gz')
        eq_(1, len(fu._filters))
        assert fu._filters[0]('./test/data/HASH.zip')
        assert not fu._filters[0]('./test/data/HASH.gz')

    def test_where_name_matches(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.where_name_matches('.*\.gz')
        eq_(1, len(fu._filters))
        assert fu._filters[0]('./test/data/HASH.gz')
        assert not fu._filters[0]('./test/data/HASH.zip')

    def test_where_name_is(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.where_name_is('HASH.gz')
        eq_(1, len(fu._filters))
        assert fu._filters[0]('./test/data/HASH.gz')
        assert not fu._filters[0]('./test/data/HASH.zip')

    def test_where_name_is_not(self):
        fu = FileUtil(self.builder)
        eq_(0, len(fu._filters))
        fu.where_name_is_not('HASH.gz')
        eq_(1, len(fu._filters))
        assert not fu._filters[0]('./test/data/HASH.gz')
        assert fu._filters[0]('./test/data/HASH.zip')
        assert fu._filters[0]('./test/data/junk')

    def test_under(self):
        fu = FileUtil(self.builder)
        fu.under('/tmp/path')
        eq_('/tmp/path', fu._from_path)
        fu.under('BUILD_DIR')
        eq_('/tmp/build_dir', fu._from_path)
        fu.under('test/data')
        eq_(os.path.join(os.getcwd(), 'test/data'), fu._from_path)
        fu.under('{BUILD_DIR}/php')
        eq_('/tmp/build_dir/php', fu._from_path)

    def test_into(self):
        fu = FileUtil(self.builder)
        fu.into('BUILD_DIR')
        eq_('/tmp/build_dir', fu._into_path)
        fu.under('/tmp/data')
        fu.into('new')
        eq_('/tmp/data/new', fu._into_path)
        fu.into('/tmp/test')
        eq_('/tmp/test', fu._into_path)
        fu.into('{BUILD_DIR}/php')
        eq_('/tmp/build_dir/php', fu._into_path)

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

    def test_done_works_copy(self):
        tmp = os.path.join(tempfile.gettempdir(), 'test_done_works')
        try:
            fu = FileUtil(self.builder)
            fu.under('./test/data')
            fu.into(tmp)
            fu.done()
            eq_(19, len(os.listdir(tmp)))
            assert os.path.exists(tmp + '/HASH')
            assert os.path.isfile(tmp + '/HASH')
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
            eq_(19, len(os.listdir(tmp1)))
            fu = FileUtil(self.builder, move=True)
            fu.under(tmp1)
            fu.into(tmp2)
            fu.done()
            eq_(0, len(os.listdir(tmp1)))
            eq_(19, len(os.listdir(tmp2)))
            assert os.path.exists(tmp2 + '/HASH')
            assert os.path.isfile(tmp2 + '/HASH')
            assert os.path.exists(tmp2 + '/config')
            assert os.path.isdir(tmp2 + '/config')
            eq_(2, len(os.listdir(tmp2 + '/config')))
        finally:
            if os.path.exists(tmp1):
                shutil.rmtree(tmp1)
            if os.path.exists(tmp2):
                shutil.rmtree(tmp2)

    def test_done_with_filters(self):
        tmp = os.path.join(tempfile.gettempdir(), 'test_done_works')
        try:
            fu = FileUtil(self.builder)
            fu.under('./test/data')
            fu.into(tmp)
            fu.any_true()
            fu.where_name_is('HASH')
            fu.where_name_is('HASH.zip')
            fu.where_name_is('options.json')
            fu.done()
            eq_(5, len(os.listdir(tmp)))
            assert os.path.exists(tmp + '/HASH')
            assert os.path.isfile(tmp + '/HASH')
            assert os.path.exists(tmp + '/HASH.zip')
            assert os.path.isfile(tmp + '/HASH.zip')
            assert os.path.exists(tmp + '/options.json')
            assert os.path.isfile(tmp + '/options.json')
            assert os.path.exists(tmp + '/config')
            assert os.path.isdir(tmp + '/config')
            assert os.path.exists(tmp + '/config/options.json')
            assert os.path.isfile(tmp + '/config/options.json')
            eq_(1, len(os.listdir(tmp + '/config')))
            assert os.path.exists(tmp + '/defaults')
            assert os.path.isdir(tmp + '/defaults')
            assert os.path.exists(tmp + '/defaults/options.json')
            assert os.path.isfile(tmp + '/defaults/options.json')
            eq_(1, len(os.listdir(tmp + '/defaults')))
        finally:
            if os.path.exists(tmp):
                shutil.rmtree(tmp)

    def test_done_with_more_filters(self):
        tmp = os.path.join(tempfile.gettempdir(), 'test_done_works')
        try:
            fu = FileUtil(self.builder)
            fu.under('./test/data')
            fu.into(tmp)
            fu.all_true()
            fu.where_name_is_not('HASH')
            fu.where_name_is_not('HASH.zip')
            fu.where_name_is_not('options.json')
            fu.where_name_is_not('.DS_Store')
            fu.where_name_is_not('junk.xml')
            fu.where_name_does_not_match('^.*plugins.*$')
            fu.where_name_does_not_match('^.*HASH.*$')
            fu.done()
            eq_(4, len(os.listdir(tmp)))
            assert os.path.exists(tmp + '/config.json')
            assert os.path.exists(tmp + '/modules.txt')
            assert os.path.exists(tmp + '/app')
            assert os.path.isdir(tmp + '/app')
            eq_(1, len(os.listdir(tmp + '/app')))
            assert os.path.exists(tmp + '/app/cache-test.txt')
        finally:
            if os.path.exists(tmp):
                shutil.rmtree(tmp)

    def test_done_move_with_filters(self):
        tmp1 = os.path.join(tempfile.gettempdir(), 'test_done_works_1')
        tmp2 = os.path.join(tempfile.gettempdir(), 'test_done_works_2')
        try:
            shutil.copytree('./test/data', tmp1)
            eq_(19, len(os.listdir(tmp1)))
            fu = FileUtil(self.builder, move=True)
            fu.under(tmp1)
            fu.into(tmp2)
            fu.any_true()
            fu.where_name_is('HASH')
            fu.where_name_is('HASH.zip')
            fu.where_name_is('options.json')
            fu.done()
            # Confirm these files were skipped
            eq_(16, len(os.listdir(tmp1)))
            assert os.path.exists(tmp1 + '/HASH.gz')
            assert os.path.exists(tmp1 + '/app')
            assert os.path.exists(tmp1 + '/config/junk.xml')
            assert os.path.exists(tmp1 + '/defaults/junk.xml')
            # Confirm these files were moved
            eq_(5, len(os.listdir(tmp2)))
            assert os.path.exists(tmp2 + '/HASH')
            assert os.path.isfile(tmp2 + '/HASH')
            assert os.path.exists(tmp2 + '/HASH.zip')
            assert os.path.isfile(tmp2 + '/HASH.zip')
            assert os.path.exists(tmp2 + '/options.json')
            assert os.path.isfile(tmp2 + '/options.json')
            assert os.path.exists(tmp2 + '/config')
            assert os.path.isdir(tmp2 + '/config')
            assert os.path.exists(tmp2 + '/config/options.json')
            assert os.path.isfile(tmp2 + '/config/options.json')
            eq_(1, len(os.listdir(tmp2 + '/config')))
            assert os.path.exists(tmp2 + '/defaults')
            assert os.path.isdir(tmp2 + '/defaults')
            assert os.path.exists(tmp2 + '/defaults/options.json')
            assert os.path.isfile(tmp2 + '/defaults/options.json')
            eq_(1, len(os.listdir(tmp2 + '/defaults')))
        finally:
            if os.path.exists(tmp1):
                shutil.rmtree(tmp1)
            if os.path.exists(tmp2):
                shutil.rmtree(tmp2)


class TestRunner(object):
    def __init__(self):
        self.builder = Dingus(
            _ctx={'VERSION': '1.0.0'})

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
        eq_('TEST', r._path)
        res = r.out_of('{VERSION}')
        eq_('1.0.0', r._path)

    def test_out_of_method(self):
        method = Dingus(return_value='TEST')
        r = Runner(self.builder)
        res = r.out_of(method)
        assert res is r
        assert 'TEST' == r._path

    def test_out_of_key(self):
        r = Runner(self.builder)
        res = r.out_of('VERSION')
        assert res is r
        eq_('1.0.0', r._path)

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
            'BP_DIR': '/tmp/build_dir',
            'EXTENSIONS': []
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

    def test_with_extension(self):
        self.ctx['EXTENSIONS'].append(
            os.path.abspath('test/data/plugins/test1'))
        b = StartScriptBuilder(self.builder)
        expectedFile = None
        try:
            b.write()
            expectedFile = os.path.join(tempfile.gettempdir(),
                                        'start.sh')
            assert os.path.exists(expectedFile)
            eq_('0755', oct(stat.S_IMODE(os.lstat(expectedFile).st_mode)))
            data = open(expectedFile, 'rt').read()
            assert data.find('ls -l') >= 0
        finally:
            if expectedFile and os.path.exists(expectedFile):
                os.remove(expectedFile)

    def test_wait_forever(self):
        b = StartScriptBuilder(self.builder)
        b.manual('ls -la')
        b.manual('echo Hello World')
        b.manual('X=1234')
        expectedFile = None
        try:
            b.write(wait_forever=True)
            expectedFile = os.path.join(tempfile.gettempdir(),
                                        'start.sh')
            assert os.path.exists(expectedFile)
            eq_('0755', oct(stat.S_IMODE(os.lstat(expectedFile).st_mode)))
            data = open(expectedFile, 'rt').read()
            assert data.find('ls -la') >= 0
            assert data.find('echo') >= 0
            assert data.find('1234') >= 0
            assert data.find('while') >= 0
            assert data.find('sleep') >= 0
            assert data.find('done') >= 0
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

    def test_value_string_formatted(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        evb.name('TEST')
        res = evb.value('test/{VAL}')
        assert res is self.ssb
        eq_('TEST=test/1234', self.ssb.calls()[0].args[0])

    def test_value_config(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        evb.name('TEST')
        res = evb.value('VAL')
        assert res is self.ssb
        eq_('TEST=1234', self.ssb.calls()[0].args[0])

    def test_from_context(self):
        evb = EnvironmentVariableBuilder(self.ssb)
        res = evb.from_context('BUILD_DIR')
        assert res is self.ssb
        eq_('BUILD_DIR=$HOME', self.ssb.calls()[0].args[0])
        res = evb.from_context('BP_DIR')
        eq_('BP_DIR=/tmp/bp_dir', self.ssb.calls()[1].args[0])


class TestBuilder(object):
    def test_release(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        old_sysargv = sys.argv
        new_sysargv = ['/tmp/build', '/tmp/bp_dir']
        try:
            sys.argv = new_sysargv
            sys.stdout = new_sysout
            b = Builder()
            b.configure()
            b.release()
        finally:
            sys.argv = old_sysargv
            sys.stdout = old_sysout
        lines = new_sysout.getvalue().split('\n')
        assert 3 == len(lines)
        eq_('default_process_types:', lines[0])
        eq_('  web: $HOME/start.sh', lines[1])

    def test_release_custom_script(self):
        old_sysout = sys.stdout
        new_sysout = StringIO()
        old_sysargv = sys.argv
        new_sysargv = ['/tmp/build', '/tmp/bp_dir']
        try:
            sys.argv = new_sysargv
            sys.stdout = new_sysout
            b = Builder()
            b.configure()
            b._ctx['START_SCRIPT_NAME'] = '$HOME/my-start-script.sh'
            b.release()
        finally:
            sys.argv = old_sysargv
            sys.stdout = old_sysout
        lines = new_sysout.getvalue().split('\n')
        assert 3 == len(lines)
        eq_('default_process_types:', lines[0])
        eq_('  web: $HOME/my-start-script.sh', lines[1])
        eq_('', lines[2])


class TestBuildPackManager(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': '/tmp/build_dir',
            'BP_DIR': '/tmp/bp_dir',
            'CACHE_DIR': '/tmp/cache_dir'
        }
        self.builder = Dingus(_ctx=self.ctx)

    def test_from_buildpack(self):
        em = BuildPackManager(self.builder)
        em.from_buildpack(
            'https://github.com/dmikusa-pivotal/cf-test-buildpack')
        em.using_branch(None)
        old_sysout = sys.stdout
        new_sysout = StringIO()
        try:
            sys.stdout = new_sysout
            em.done()
        finally:
            sys.stdout = old_sysout
            if os.path.exists(em._bp.bp_dir):
                shutil.rmtree(em._bp.bp_dir)
        output = new_sysout.getvalue()
        eq_(True, output.find('Listing Environment:') > -1)
        eq_(True, output.find('CPU Info') > -1)


class TestExtensionInstaller(object):
    def __init__(self):
        self.ctx = {
            'BUILD_DIR': '/tmp/build_dir',
            'BP_DIR': '/tmp/bp_dir',
            'CACHE_DIR': '/tmp/cache_dir',
            'PLUGIN': 'plugins',
            'EXTENSIONS': []
        }
        self.builder = Dingus(_ctx=self.ctx)
        self.inst = Dingus(builder=self.builder)

    def test_from_location(self):
        ei = ExtensionInstaller(self.inst)
        eq_(0, len(ei._paths))
        ei.from_path('test/data/plugins/test1')
        eq_(1, len(ei._paths))

    def test_from_directory(self):
        ei = ExtensionInstaller(self.inst)
        eq_(0, len(ei._paths))
        ei.from_path('test/data/plugins')
        eq_(3, len(ei._paths))

    def test_from_path_with_format(self):
        ei = ExtensionInstaller(self.inst)
        eq_(0, len(ei._paths))
        ei.from_path('test/data/{PLUGIN}')
        eq_(3, len(ei._paths))

    def test_works(self):
        ei = ExtensionInstaller(self.inst)
        ei.from_path('test/data/plugins/test1')
        eq_(0, len(self.ctx['EXTENSIONS']))
        ei.done()
        eq_(1, len(self.ctx['EXTENSIONS']))
        eq_(os.path.abspath('test/data/plugins/test1'),
            self.ctx['EXTENSIONS'][0])

    def test_fails_retcode(self):
        ei = ExtensionInstaller(self.inst)
        ei.from_path('test/data/plugins/test2')
        ei.ignore_errors(False)
        try:
            ei.done()
            assert False, "should not reach this code"
        except RuntimeError, e:
            eq_('Extension Failed with [-1]', str(e))

    def test_fails_exception(self):
        ei = ExtensionInstaller(self.inst)
        ei.from_path('test/data/plugins/test3')
        ei.ignore_errors(False)
        try:
            ei.done()
            assert False, "should not reach this code"
        except ValueError, e:
            eq_('Intentional', str(e))


class TestModuleInstaller(object):
    def setUp(self):
        self.ctx = utils.FormattedDict({
            'CACHE_HASH_ALGORITHM': 'sha1',
            'LOCAL_MODULES_PATTERN': 'pattern/{MODULE_NAME}',
            'BUILD_DIR': 'test/data',
            'BP_DIR': '/tmp/bp_dir',
            'CACHE_DIR': '/tmp/cache_dir'
        })
        self.builder = Dingus(_ctx=self.ctx)
        self.inst = Dingus(builder=self.builder)

    def tearDown(self):
        pass

    def test_default_load_modules(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        res = mi._default_load_method('test/data/modules.txt')
        eq_(3, len(res))
        eq_('Module1', res[0])
        eq_('Module2', res[1])
        eq_('Module3', res[2])
        res = mi._load_modules('test/data/modules.txt')
        eq_(3, len(res))
        eq_('Module1', res[0])
        eq_('Module2', res[1])
        eq_('Module3', res[2])

    def test_regex_load_method(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        mi.find_modules_with_regex(r'(.*)')
        res = mi._regex_load_method('test/data/modules.txt')
        eq_(3, len(res))
        eq_('Module1', res[0])
        eq_('Module2', res[1])
        eq_('Module3', res[2])
        res = mi._load_modules('test/data/modules.txt')
        eq_(3, len(res))
        eq_('Module1', res[0])
        eq_('Module2', res[1])
        eq_('Module3', res[2])

    def test_filter_files_by_extension(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        res = mi.filter_files_by_extension('.conf')
        eq_(mi, res)
        eq_('.conf', mi._extn)

    def test_include_module(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        mi.include_module('test1')
        res = mi.include_module('test2')
        eq_(mi, res)
        eq_(2, len(mi._modules))
        eq_('test1', mi._modules[0])
        eq_('test2', mi._modules[1])

    def test_find_modules_with(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        method = Dingus()
        eq_(mi._default_load_method, mi._load_modules)
        res = mi.find_modules_with(method)
        eq_(mi, res)
        eq_(method, mi._load_modules)

    def test_find_modules_with_regex(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        eq_(mi._default_load_method, mi._load_modules)
        res = mi.find_modules_with_regex(r'(.*)')
        eq_(mi, res)
        eq_(mi._regex_load_method, mi._load_modules)

    def test_from_application_file(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        res = mi.from_application('modules.txt')
        eq_(mi, res)
        eq_(3, len(mi._modules))
        eq_(True, 'Module1' in mi._modules)
        eq_(True, 'Module2' in mi._modules)
        eq_(True, 'Module3' in mi._modules)

    def test_from_application_directory(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        mi.filter_files_by_extension('.txt')
        res = mi.from_application('')
        eq_(mi, res)
        eq_(3, len(mi._modules))
        eq_(True, 'Module1' in mi._modules)
        eq_(True, 'Module2' in mi._modules)
        eq_(True, 'Module3' in mi._modules)

    def test_done(self):
        mi = ModuleInstaller(self.inst, 'LOCAL')
        mi._cf = Dingus()
        mi.filter_files_by_extension('.txt')
        mi.from_application('')
        mi.done()
        eq_(3, len(mi._cf.install_binary_direct.calls()))
        for mod, call in zip(mi._modules, mi._cf.install_binary_direct.calls):
            eq_(4, len(call.args))
            eq_('pattern/%s' % mod, call.args[0])
            eq_('pattern/%s.sha1' % mod, call.args[1])
            eq_('test/data/local', call.args[2])
            eq_(False, call.args[3])


class TestSaveBuilder(object):
    def setUp(self):
        self.ctx = {
            'BUILD_DIR': os.path.join(tempfile.gettempdir(), 'save-builder'),
            'EXTENSIONS': [os.path.abspath('test/data/plugins/test1'),
                           os.path.abspath('test/data/plugins/test2')]
        }
        self.builder = Dingus(_ctx=self.ctx)
        os.makedirs(self.ctx['BUILD_DIR'])

    def tearDown(self):
        if os.path.exists(self.ctx['BUILD_DIR']):
            shutil.rmtree(self.ctx['BUILD_DIR'])

    @with_setup(setup=setUp, teardown=tearDown)
    def test_runtime_environment(self):
        sb = SaveBuilder(self.builder)
        res = sb.runtime_environment()
        eq_(sb, res)
        envFile = os.path.join(self.ctx['BUILD_DIR'], '.env')
        eq_(True, os.path.exists(envFile))
        with open(envFile, 'rt') as f:
            lines = f.readlines()
            eq_(2, len(lines))
            eq_('TEST_ENV=1234\n', lines[0])
            eq_('TEST_ENV=4321\n', lines[1])

    @with_setup(setup=setUp, teardown=tearDown)
    def test_process_list(self):
        sb = SaveBuilder(self.builder)
        res = sb.process_list()
        eq_(sb, res)
        procFile = os.path.join(self.ctx['BUILD_DIR'], '.procs')
        eq_(True, os.path.exists(procFile))
        with open(procFile, 'rt') as f:
            lines = f.readlines()
            eq_(2, len(lines))
            eq_('server: sleep 1\n', lines[0])
            eq_('server: sleep 2\n', lines[1])

import os
import shutil
import tempfile
import json
from dingus import Dingus
from nose.tools import eq_
from nose.tools import raises
from build_pack_utils import utils


class TestLoadEnv(object):
    def test_load_env(self):
        env = utils.load_env('test/data/env.txt')
        eq_(3, len(env.keys()))
        eq_(True, 'x' in env.keys())
        eq_(True, 'y' in env.keys())
        eq_(True, 'z' in env.keys())
        eq_('1234', env['x'])
        eq_('5678', env['y'])
        eq_('90ab', env['z'])


class TestLoadProcesses(object):
    def test_load_procs(self):
        procs = utils.load_processes('test/data/procs.txt')
        eq_(3, len(procs.keys()))
        eq_(True, 'ls' in procs.keys())
        eq_(True, 'echo' in procs.keys())
        eq_(True, 'server' in procs.keys())
        eq_('ls -la', procs['ls'])
        eq_("echo 'Hello World!'", procs['echo'])
        eq_('python start_server.py', procs['server'])


class TestLoadExtension(object):
    def test_load_test1(self):
        test1 = utils.load_extension('test/data/plugins/test1')
        res = test1.service_environment({})
        eq_('1234', res['TEST_ENV'])

    def test_load_test5(self):
        test5 = utils.load_extension('test/data/plugins/test5')
        ctx = {}
        res = test5.configure(ctx)
        assert res is None
        assert 'ADDED_BY_EXTENSION' in ctx.keys()
        assert ctx['ADDED_BY_EXTENSION']

    def test_load_test4(self):
        test4 = utils.load_extension('test/data/plugins/test4')
        ctx = {}
        try:
            test4.configure(ctx)
        except ValueError, e:
            eq_('Intentional', str(e))

    def test_load_test3(self):
        test3 = utils.load_extension('test/data/plugins/test3')
        assert not hasattr(test3, 'configure')

    def test_load_test4then3(self):
        test4 = utils.load_extension('test/data/plugins/test4')
        ctx = {}
        try:
            test4.configure(ctx)
        except ValueError, e:
            eq_('Intentional', str(e))
        test3 = utils.load_extension('test/data/plugins/test3')
        assert not hasattr(test3, 'configure')

    def test_load_without_init(self):
        try:
            os.remove('test/data/plugins/test5/__init__.py')
            os.remove('test/data/plugins/test5/__init__.pyc')
        except IOError:
            pass
        utils.load_extension('test/data/plugins/test5')
        assert os.path.exists('test/data/plugins/test5/__init__.py')


class TestProcessExtensions(object):
    def test_process_extension(self):
        process = Dingus()
        ctx = {'EXTENSIONS': ['test/data/plugins/test1']}
        utils.process_extensions(ctx, 'service_environment', process)
        eq_(1, len(process.calls()))
        eq_('1234', process.calls()[0].args[0]['TEST_ENV'])

    def test_process_extensions(self):
        process = Dingus()
        ctx = {'EXTENSIONS': ['test/data/plugins/test1',
                              'test/data/plugins/test2']}
        utils.process_extensions(ctx, 'service_environment', process)
        eq_(2, len(process.calls()))
        eq_('1234', process.calls()[0].args[0]['TEST_ENV'])
        eq_('4321', process.calls()[1].args[0]['TEST_ENV'])

    def test_process_extension_with_custom_args(self):
        compile = Dingus(return_value=0)
        extn = Dingus(compile=compile)
        process = Dingus()
        args = [Dingus(), Dingus()]
        load_extension = utils.load_extension
        utils.load_extension = Dingus(return_value=extn)
        ctx = {'EXTENSIONS': ['doesnt matter']}
        try:
            utils.process_extensions(ctx, 'compile', process, args=args)
            eq_(1, len(process.calls()))
            eq_(1, len(utils.load_extension.calls()))
            eq_(1, len(compile.calls()))
            eq_(2, len(compile.calls()[0].args))
            eq_(args[0], compile.calls()[0].args[0])
            eq_(args[1], compile.calls()[0].args[1])
            eq_(1, len(process.calls()))
            eq_(1, len(process.calls()[0].args))
            eq_(0, process.calls()[0].args[0])
        finally:
            utils.load_extension = load_extension


class TestRewriteCfgs(object):
    def setUp(self):
        self.cfgs = os.path.join(tempfile.gettempdir(), 'rewrite-cfgs')
        os.makedirs(os.path.join(self.cfgs, 'subdir'))
        shutil.copy('test/data/test.cfg', self.cfgs)
        shutil.copy('test/data/test.cfg', os.path.join(self.cfgs, 'subdir'))

    def tearDown(self):
        if os.path.exists(self.cfgs):
            shutil.rmtree(self.cfgs)

    def assert_cfg_fresh(self, path):
        lines = open(path).readlines()
        eq_(9, len(lines))
        eq_('#{HOME}/test.cfg\n', lines[0])
        eq_('@{TMPDIR}/some-file.txt\n', lines[1])
        eq_('${TMPDIR}\n', lines[2])
        eq_('#{DNE}/test.txt\n', lines[3])
        eq_('@{DNE}/test.txt\n', lines[4])
        eq_('${DNE}/test.txt\n', lines[5])
        eq_('#{SOMEPATH}\n', lines[6])
        eq_('@{SOMEPATH}\n', lines[7])

    def assert_cfg_std(self, path):
        lines = open(path).readlines()
        eq_(9, len(lines))
        eq_('/home/user/test.cfg\n', lines[0])
        eq_('@{TMPDIR}/some-file.txt\n', lines[1])
        eq_('${TMPDIR}\n', lines[2])
        eq_('#{DNE}/test.txt\n', lines[3])
        eq_('@{DNE}/test.txt\n', lines[4])
        eq_('${DNE}/test.txt\n', lines[5])
        eq_('/tmp/path\n', lines[6])
        eq_('@{SOMEPATH}\n', lines[7])

    def assert_cfg_custom(self, path):
        lines = open(path).readlines()
        eq_(9, len(lines))
        eq_('#{HOME}/test.cfg\n', lines[0])
        eq_('/tmp/some-file.txt\n', lines[1])
        eq_('${TMPDIR}\n', lines[2])
        eq_('#{DNE}/test.txt\n', lines[3])
        eq_('@{DNE}/test.txt\n', lines[4])
        eq_('${DNE}/test.txt\n', lines[5])
        eq_('#{SOMEPATH}\n', lines[6])
        eq_('/tmp/path\n', lines[7])

    def test_rewrite_defaults(self):
        ctx = utils.FormattedDict({
            'TMPDIR': '/tmp',
            'HOME': '/home/user',
            'SOMEPATH': '{TMPDIR}/path'
        })
        utils.rewrite_cfgs(self.cfgs, ctx)
        self.assert_cfg_std(os.path.join(self.cfgs, 'test.cfg'))
        self.assert_cfg_std(os.path.join(self.cfgs, 'subdir', 'test.cfg'))

    def test_rewrite_file(self):
        ctx = utils.FormattedDict({
            'TMPDIR': '/tmp',
            'HOME': '/home/user',
            'SOMEPATH': '{TMPDIR}/path'
        })
        utils.rewrite_cfgs(os.path.join(self.cfgs, 'test.cfg'), ctx)
        self.assert_cfg_std(os.path.join(self.cfgs, 'test.cfg'))
        self.assert_cfg_fresh(os.path.join(self.cfgs, 'subdir', 'test.cfg'))

    def test_rewrite_custom_delimiter(self):
        ctx = utils.FormattedDict({
            'TMPDIR': '/tmp',
            'HOME': '/home/user',
            'SOMEPATH': '{TMPDIR}/path'
        })
        utils.rewrite_cfgs(self.cfgs, ctx, delim='@')
        self.assert_cfg_custom(os.path.join(self.cfgs, 'test.cfg'))
        self.assert_cfg_custom(os.path.join(self.cfgs, 'subdir', 'test.cfg'))


class TestCopytree(object):
    def setUp(self):
        self.toDir = tempfile.mkdtemp(prefix='copytree-')

    def tearDown(self):
        if os.path.exists(self.toDir):
            shutil.rmtree(self.toDir)

    def assert_exists(self, path):
        eq_(True, os.path.exists(os.path.join(self.toDir, path)))

    def test_copytree_dirs(self):
        fromDir = 'test/data/plugins'
        utils.copytree(fromDir, self.toDir)
        self.assert_exists(self.toDir)
        self.assert_exists(os.path.join(self.toDir, 'test1'))
        self.assert_exists(os.path.join(self.toDir, 'test2'))
        self.assert_exists(os.path.join(self.toDir, 'test3'))

    def test_copytree_flat(self):
        fromDir = 'test/data/.bp-config'
        utils.copytree(fromDir, self.toDir)
        self.assert_exists(self.toDir)
        self.assert_exists(os.path.join(self.toDir, 'options.json'))
        self.assert_exists(os.path.join(self.toDir, 'junk.xml'))


class TestFormattedDict(object):
    def test_empty(self):
        x = utils.FormattedDict()
        eq_(0, len(x.keys()))

    def test_basics(self):
        x = utils.FormattedDict({
            'A': 1234,
            'B': 5678
        })
        eq_(1234, x['A'])
        eq_(5678, x['B'])
        eq_(1234, x.get('A'))
        eq_(5678, x.get('B'))
        eq_(None, x.get('C'))
        eq_(0, x.get('C', 0))

    def test_kwargs(self):
        x = utils.FormattedDict(A=1234, B=5678)
        eq_(1234, x['A'])
        eq_(5678, x['B'])
        eq_(1234, x.get('A'))
        eq_(5678, x.get('B'))
        eq_(None, x.get('C'))
        eq_(0, x.get('C', 0))

    def test_formatted(self):
        x = utils.FormattedDict(A=1234, B=5678, C='{A}')
        eq_('1234', x['C'])
        eq_('1234', x.get('C'))

    def test_complicated(self):
        x = utils.FormattedDict({
            'A': 1234,
            'B': 5678,
            'C': '{A}/{B}',
            'D': '{C}/{B}',
            'E': '{D}/{C}'
        })
        eq_(1234, x['A'])
        eq_(5678, x['B'])
        eq_('1234/5678', x['C'])
        eq_('1234/5678/5678', x['D'])
        eq_('1234/5678', x.get('C'))
        eq_('1234/5678/5678', x.get('D'))
        eq_('1234/5678', x.get('C', None))
        eq_('1234/5678/5678', x.get('D', None))
        eq_('1234/5678/5678/1234/5678', x['E'])
        eq_('1234/5678/5678/1234/5678', x.get('E'))
        eq_('1234/5678/5678/1234/5678', x.get('E', None))
        eq_(None, x.get('F', None))

    def test_plain(self):
        x = utils.FormattedDict({
            'A': 1234,
            'B': 5678,
            'C': '{A}/{B}',
            'D': '{C}/{B}',
            'E': '{D}/{C}'
        })
        eq_(1234, x.get('A', format=False))
        eq_(5678, x.get('B', format=False))
        eq_('{A}/{B}', x.get('C', format=False))
        eq_('1234/5678', x.get('C', format=True))

    def test_json(self):
        x = utils.FormattedDict({
            'DATA': utils.wrap(json.dumps({'x': 1}))
        })
        eq_('{"x": 1}', x['DATA'])

    def test_place_holder_wrapped(self):
        x = utils.FormattedDict({
            'DATA': utils.wrap('{some_key}')
        })
        eq_('{some_key}', x['DATA'])

    @raises(KeyError)
    def test_place_holder(self):
        x = utils.FormattedDict({
            'DATA': '{some_key}'
        })
        assert '{some_key}' != x['DATA']

    def test_get_with_format_false(self):
        x = utils.FormattedDict({
            'DATA': utils.wrap('{some_key}')
        })
        data = x.get('DATA', format=False)
        assert not hasattr(data, 'unwrap'), \
            "should not be a wrapper object"
        assert "{some_key}" == data, "data should match"


class TestFindBpUrl(object):
    def setUp(self):
        self.this_project = os.path.dirname(os.path.dirname(__file__))

    def testThisProject(self):
        git_url = utils.find_git_url(self.this_project)
        assert git_url.startswith(
            'git@github.com:dmikusa-pivotal/py-cf-buildpack-utils.git#')

    def testNotGitProject(self):
        git_url = utils.find_git_url(os.path.join(self.this_project, 'test'))
        eq_(None, git_url)

    def testNoGitInstalled(self):
        old_path = os.environ['PATH']
        os.environ['PATH'] = ''
        try:
            git_url = utils.find_git_url(self.this_project)
            eq_(None, git_url)
        finally:
            os.environ['PATH'] = old_path

    def testSomeOtherGitDir(self):
        prj_git_url = utils.find_git_url(self.this_project)
        git_url = utils.find_git_url(
            os.path.join(
                os.path.dirname(self.this_project),
                'cf-php-build-pack'))
        assert prj_git_url != git_url


class TestConfigFileEditor(object):
    def test_find_lines_matching(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php-fpm.conf')
        lines = cfg.find_lines_matching(r'^pid =')
        eq_(1, len(lines))
        eq_('pid = @{HOME}/php/var/run/php-fpm.pid', lines[0])

    @raises(ValueError)
    def test_find_lines_matching_bad_expression(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php-fpm.conf')
        cfg.find_lines_matching([])

    def test_find_lines_matching_multiple(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php.ini')
        lines = cfg.find_lines_matching(r'^mssql.')
        eq_(7, len(lines))
        eq_('mssql.allow_persistent = On', lines[0])
        eq_('mssql.max_persistent = -1', lines[1])
        eq_('mssql.max_links = -1', lines[2])

    def test_update_lines(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php.ini')
        cfg.update_lines(
            r'^mssql.max_links = -1',
            'mssql.max_links = 5')
        lines = cfg.find_lines_matching(r'^mssql.max_links')
        eq_(1, len(lines))
        eq_('mssql.max_links = 5', lines[0])

    @raises(ValueError)
    def test_update_lines_bad_expression(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php-fpm.conf')
        cfg.update_lines([], '')

    def test_append(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php-fpm.conf')
        eq_(517, len(cfg._lines))
        cfg.append_lines(['test=1', 'test=2'])
        eq_(519, len(cfg._lines))

    def test_append_after_found(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php.ini')
        eq_(1822, len(cfg._lines))
        cfg.insert_after(
            r'^mssql.max_links = -1',
            ['test=1', 'test=2'])
        eq_(1824, len(cfg._lines))
        eq_('mssql.max_links = -1\n', cfg._lines[1590])
        eq_('test=1\n', cfg._lines[1591])
        eq_('test=2\n', cfg._lines[1592])

    def test_append_after_not_found(self):
        cfg = utils.ConfigFileEditor('test/data/defaults/php.ini')
        eq_(1822, len(cfg._lines))
        cfg.insert_after(
            r'^aldsjfjdfkdjf',
            ['test=1', 'test=2'])
        eq_(1822, len(cfg._lines))

    def test_save(self):
        try:
            expected = os.path.join(tempfile.gettempdir(), 'php-fpm-new.conf')
            cfg = utils.ConfigFileEditor('test/data/defaults/php-fpm.conf')
            cfg.save(expected)
            cfgNew = utils.ConfigFileEditor(expected)
            for lineA, lineB in zip(cfg._lines, cfgNew._lines):
                eq_(lineA, lineB)
        finally:
            if os.path.exists(expected):
                os.remove(expected)


class TestUnique(object):
    def test_no_change(self):
        x = [6, 5, 7, 8, 9, 3, 2, 1]
        y = utils.unique(x)
        assert len(x) == len(y)
        assert [a == b for a, b in zip(x, y)]

    def test_all_dups(self):
        x = [1, 1, 1, 1, 1, 1, 1]
        y = utils.unique(x)
        assert len(y) == 1
        assert y[0] == 1

    def test_order_is_the_same(self):
        x = [6, 5, 7, 6, 8, 9, 2, 2, 7, 5, 1, 9, 1, 6, 7, 0]
        y = utils.unique(x)
        assert len(y) == 8
        assert y[0] == 6
        assert y[1] == 5
        assert y[2] == 7
        assert y[3] == 8
        assert y[4] == 9
        assert y[5] == 2
        assert y[6] == 1
        assert y[7] == 0

import os
import shutil
import tempfile
import json
from dingus import Dingus
from nose.tools import eq_
from nose.tools import with_setup
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
        eq_(8, len(lines))
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
        eq_(8, len(lines))
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
        eq_(8, len(lines))
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

    @with_setup(setup=setUp, teardown=tearDown)
    def test_copytree_dirs(self):
        fromDir = 'test/data/plugins'
        utils.copytree(fromDir, self.toDir)
        self.assert_exists(self.toDir)
        self.assert_exists(os.path.join(self.toDir, 'test1'))
        self.assert_exists(os.path.join(self.toDir, 'test2'))
        self.assert_exists(os.path.join(self.toDir, 'test3'))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_copytree_flat(self):
        fromDir = 'test/data/config'
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

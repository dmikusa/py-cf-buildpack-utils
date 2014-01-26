import os.path
import tempfile
import shutil
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import runner


TEST_BP = 'https://github.com/dmikusa-pivotal/cf-test-buildpack'
TEST_APP = 'test/data/app'


class TestRunner(object):
    def __init__(self):
        self._cwd = os.getcwd()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='bp-test')
        self.ctx = {
            'BUILD_DIR': os.path.join(self.root, 'build'),
            'CACHE_DIR': os.path.join(self.root, 'cache')
        }
        os.chdir(self._cwd)
        shutil.copytree(TEST_APP, self.ctx['BUILD_DIR'])
        self.bp = runner.BuildPack(self.ctx, TEST_BP)

    def tearDown(self):
        if os.path.exists(self.root):
            shutil.rmtree(self.root)
        if os.path.exists(self.bp.bp_dir):
            shutil.rmtree(self.bp.bp_dir)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_clone(self):
        self.bp._clone()
        eq_(True, os.path.exists(self.bp.bp_dir))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir, 'bin')))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir,
                                              'bin', 'compile')))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir,
                                              'bin', 'release')))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir,
                                              'bin', 'detect')))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_detect(self):
        self.bp._clone()
        res = self.bp._detect()
        eq_('CACHETEST', res)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_detect_fail(self):
        self.bp._clone()
        os.remove(os.path.join(self.ctx['BUILD_DIR'], 'cache-test.txt'))
        try:
            self.bp._detect()
            assert "Should Fail!", False
        except Exception, e:
            eq_(155, str(e).find('returned non-zero exit status 1'))
            eq_('no\n', e.output)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_compile(self):
        self.bp._clone()
        output = self.bp._compile()
        eq_(True, output.startswith('Running cache test...'))
        eq_(859, output.find('Listing Environment:'))
        eq_(4169, output.find('CPU Info'))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_release(self):
        self.bp._clone()
        output = self.bp._release()
        eq_(True, output.startswith('---'))
        eq_(29, output.find('web: ./start.sh'))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_run(self):
        self.bp.run()

import sys
import os
import tempfile
import shutil
from nose.tools import with_setup
from nose.tools import eq_
from build_pack_utils import CloudFoundryUtil
from build_pack_utils import CloudFoundryInstaller


class TestCloudFoundryInstaller(object):
    def setUp(self):
        # save the old stdout && args
        self.old_sys_argv = sys.argv
        self.old_stdout = sys.stdout
        # insert args for testinga
        self.rootDir = os.path.join(tempfile.gettempdir(), 'bp-util')
        self.buildDir = os.path.join(self.rootDir, 'build')
        self.cacheDir = os.path.join(self.rootDir, 'cache')
        sys.argv = [sys.argv[0], self.buildDir, self.cacheDir]
        # setup tests
        self.ctx = CloudFoundryUtil.initialize()
        self.ctx.update({
            "CACHE_HASH_ALGORITHM": "sha1",
            "SNAKE_PACKAGE": "snake.tar.gz",
            "HOST": "dl.dropboxusercontent.com",
            "PATH": "u/186123235/py-cf-buildpack-utils-tests",
            "SNAKE_DOWNLOAD_URL": "https://{HOST}/{PATH}/{SNAKE_PACKAGE}",
            "SNAKE_STRIP": True
        })
        assert ['.bp'] == os.listdir(self.buildDir)
        # uncomment to enforce cache is cleared every time
        #assert [] == os.listdir(self.cacheDir)

    def tearDown(self):
        # delete downloaded and temp files
        if os.path.exists(self.rootDir):
            shutil.rmtree(self.rootDir)
        snakeFile = os.path.join(os.environ['TMPDIR'], 'snake.tar.gz')
        if os.path.exists(snakeFile):
            os.remove(snakeFile)
        # uncomment to force download every time
        #if os.path.exists(self.cacheDir):
        #   shutil.rmtree(self.cacheDir)
        # Restore old stdout && args
        sys.argv = self.old_sys_argv
        sys.stdout = self.old_stdout

    @with_setup(setup=setUp, teardown=tearDown)
    def test_installer(self):
        installer = CloudFoundryInstaller(self.ctx)
        path = installer.install_binary('SNAKE')
        assert path is not None
        eq_(os.path.join(self.buildDir, 'snake'), path)
        assert os.path.exists(os.path.join(self.buildDir, 'snake',
                                           'js', 'game.js'))

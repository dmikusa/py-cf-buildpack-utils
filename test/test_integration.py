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
        # insert args for testing
        self.buildDir = os.path.join(tempfile.gettempdir(), 'bp-util', 'build')
        self.cacheDir = os.path.join(tempfile.gettempdir(), 'bp-util', 'cache')
        sys.argv = [sys.argv[0], self.buildDir, self.cacheDir]
        # setup tests
        self.ctx = CloudFoundryUtil.initialize()
        self.ctx.update(
            CloudFoundryUtil.load_json_config_file(
                '/Users/danielmikusa/Code/Python/CfMavenBuildPack/defaults/options.json'))
        assert [] == os.listdir(self.buildDir)
        # uncomment to enforce cache is cleared every time
        #assert [] == os.listdir(self.cacheDir)

    def tearDown(self):
        if os.path.exists(self.buildDir):
            shutil.rmtree(self.buildDir)
        # uncomment to force download every time
        #if os.path.exists(self.cacheDir):
        #   shutil.rmtree(self.cacheDir)
        # Restore old stdout && args
        sys.argv = self.old_sys_argv
        sys.stdout = self.old_stdout

    @with_setup(setup=setUp, teardown=tearDown)
    def test_installer(self):
        installer = CloudFoundryInstaller(self.ctx)
        path = installer.install_binary('MAVEN')
        assert path is not None
        eq_(os.path.join(self.buildDir, 'maven'), path)
        assert os.path.exists(os.path.join(self.buildDir, 'maven', 'bin', 'mvn'))

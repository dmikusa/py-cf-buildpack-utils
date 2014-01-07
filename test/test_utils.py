import os
import shutil
import tempfile
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils

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

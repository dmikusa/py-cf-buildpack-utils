import os
import tempfile
import shutil
from nose.tools import with_setup
from nose.tools import eq_
from build_pack_utils import UnzipUtil
from build_pack_utils import HashUtil


class TestUnzipUtil(object):

    HASH_FILE = './test/data/HASH'
    HASH_FILE_ZIP = './test/data/HASH.zip'
    HASH_FILE_WAR = './test/data/HASH.war'
    HASH_FILE_JAR = './test/data/HASH.jar'
    HASH_FILE_STRIP_ZIP = './test/data/HASH-STRIP.zip'
    HASH_FILE_BZ2 = './test/data/HASH.bz2'
    HASH_FILE_GZ = './test/data/HASH.gz'
    HASH_FILE_TAR = './test/data/HASH.tar'
    HASH_FILE_TARGZ = './test/data/HASH.tar.gz'
    HASH_FILE_STRIP_TARGZ = './test/data/HASH.tar.gz'
    HASH_FILE_TARBZ2 = './test/data/HASH.tar.bz2'
    HASH_FILE_STRIP_TARBZ2 = './test/data/HASH.tar.bz2'

    def __init__(self):
        self._hshUtil = HashUtil(
            {'CACHE_HASH_ALGORITHM': 'sha256'})
        self._hash = self._hshUtil.calculate_hash(self.HASH_FILE)

    def setUp(self):
        self._dir = os.path.join(tempfile.gettempdir(), 'zip-test')
        if not os.path.exists(self._dir):
            os.makedirs(self._dir)
        self._path = os.path.join(self._dir, 'HASH')

    def tearDown(self):
        if os.path.exists(self._dir):
            shutil.rmtree(self._dir)

    def run_method(self, method, path):
        uzUtil = UnzipUtil({'TMPDIR': tempfile.gettempdir()})
        path = os.path.abspath(path)
        outPath = getattr(uzUtil, method)(path, self._dir, 0)
        assert len(outPath) > 0
        if method == '_gunzip' or method == '_bunzip2':
            assert outPath.endswith('HASH')
        else:
            assert 1 == len(os.listdir(outPath))
            assert 'HASH' == os.listdir(outPath)[0]
        assert outPath.startswith(self._dir)
        assert os.path.exists(self._path)
        assert self._hash == self._hshUtil.calculate_hash(self._path)

    def run_method_strip(self, method, path):
        uzUtil = UnzipUtil({'TMPDIR': tempfile.gettempdir()})
        path = os.path.abspath(path)
        outPath = getattr(uzUtil, method)(path, self._dir, 1)
        assert len(outPath) > 0
        assert 1 == len(os.listdir(outPath))
        assert 'HASH' == os.listdir(outPath)[0]
        assert outPath.startswith(self._dir)
        assert os.path.exists(self._path)
        assert self._hash == self._hshUtil.calculate_hash(self._path)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_unzip(self):
        self.run_method('_unzip', self.HASH_FILE_ZIP)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_unzip_strip_level(self):
        self.run_method_strip('_unzip', self.HASH_FILE_STRIP_ZIP)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_untar(self):
        self.run_method('_untar', self.HASH_FILE_TAR)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_gunzip(self):
        self.run_method('_gunzip', self.HASH_FILE_GZ)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_bunzip2(self):
        self.run_method('_bunzip2', self.HASH_FILE_BZ2)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_tar_gunzip(self):
        self.run_method('_tar_gunzip', self.HASH_FILE_TARGZ)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_tar_bunzip2(self):
        self.run_method('_tar_bunzip2', self.HASH_FILE_TARBZ2)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_extract(self):
        uzUtil = UnzipUtil({})
        outPath = uzUtil.extract(self.HASH_FILE_ZIP, self._dir)
        assert len(outPath) > 0
        assert outPath.startswith(self._dir)
        assert os.path.exists(self._path)
        assert self._hash == self._hshUtil.calculate_hash(self._path)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_extract_force_strip_not_needed(self):
        uzUtil = UnzipUtil({})
        outPath = uzUtil.extract(self.HASH_FILE_ZIP, self._dir, strip=True)
        assert len(outPath) > 0
        assert outPath.startswith(self._dir)
        assert os.path.exists(self._path)
        assert self._hash == self._hshUtil.calculate_hash(self._path)
        tmpDir = tempfile.gettempdir()
        eq_(0, len([f for f in os.listdir(tmpDir) if f.startswith('zips-')]))

    def test_pick_based_on_file_extension(self):
        uzUtil = UnzipUtil({})
        assert uzUtil._unzip == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_ZIP)
        assert uzUtil._untar == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_TAR)
        assert uzUtil._gunzip == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_GZ)
        assert uzUtil._bunzip2 == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_BZ2)
        assert uzUtil._tar_gunzip == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_TARGZ)
        assert uzUtil._tar_bunzip2 == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_TARBZ2)
        assert uzUtil._unzip == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_WAR)
        assert uzUtil._unzip == \
            uzUtil._pick_based_on_file_extension(self.HASH_FILE_JAR)

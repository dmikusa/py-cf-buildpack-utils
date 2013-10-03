import os
import tempfile
import shutil
from nose.tools import with_setup
from build_pack_utils import UnzipUtil
from build_pack_utils import HashUtil


class TestUnzipUtil(object):

    HASH_FILE = './test/data/HASH'
    HASH_FILE_ZIP = './test/data/HASH.zip'
    HASH_FILE_BZ2 = './test/data/HASH.bz2'
    HASH_FILE_GZ = './test/data/HASH.gz'
    HASH_FILE_TAR = './test/data/HASH.tar'
    HASH_FILE_TARGZ = './test/data/HASH.tar.gz'
    HASH_FILE_TARBZ2 = './test/data/HASH.tar.bz2'

    def __init__(self):
        self._hshUtil = HashUtil(
            {'cache-hash-algorithm': 'sha256'})
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
        uzUtil = UnzipUtil({})
        outPath = getattr(uzUtil, method)(path, self._dir)
        assert len(outPath) > 0
        assert outPath.startswith(self._dir)
        assert os.path.exists(self._path)
        assert self._hash == self._hshUtil.calculate_hash(self._path)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_unzip(self):
        self.run_method('_unzip', self.HASH_FILE_ZIP)

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

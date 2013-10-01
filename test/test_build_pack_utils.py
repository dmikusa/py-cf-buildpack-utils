import build_pack_utils
import sys
import urllib2
import os.path
import tempfile
import shutil
from nose.tools import raises
from nose.tools import eq_
from nose.tools import with_setup
from dingus import Dingus


class TestDownloaderUtils(object):
    def _run_download(self, dwn, url):
        path = os.path.join(tempfile.gettempdir(), 'KEYS')
        dwn.download(url, path)
        assert os.path.exists(path)
        with open(path, 'rt') as keysFile:
            assert 11 == \
                keysFile.read().count('-----END PGP PUBLIC KEY BLOCK-----')

    def run_download(self, dwn):
        self._run_download(
            dwn,
            'http://archive.apache.org/dist/tomcat/tomcat-8/KEYS')

    def run_download_404(self, dwn):
        self._run_download(dwn, 'http://www.mikusa.com/does_not_exist')

    # Tests start here
    def test_downloader(self):
        self.run_download(build_pack_utils.Downloader({}))

    def test_downloader_verbose(self):
        self.run_download(build_pack_utils.Downloader({'verbose': True}))

    @raises(urllib2.HTTPError)
    def test_downloader_404(self):
        self.run_download_404(build_pack_utils.Downloader({}))

    def test_curl_downloader(self):
        self.run_download(build_pack_utils.CurlDownloader({}))

    @raises(RuntimeError)
    def test_curl_downloader_404(self):
        self.run_download_404(build_pack_utils.CurlDownloader({}))


class TestHashUtils(object):
    HASH_FILE = './test/data/HASH'

    def hash_file_calc(self, hsh, digest):
        assert digest == hsh.calculate_hash(self.HASH_FILE)

    def hash_file_matches(self, hsh, digest):
        assert hsh.does_hash_match(digest, self.HASH_FILE)

    def hash_file_not_matches(self, hsh, digest):
        assert not hsh.does_hash_match(digest, self.HASH_FILE)

    def hash_file_bad_algorithm(self, hsh, algorithm, msg):
        try:
            hsh.calculate_hash(self.HASH_FILE)
            assert False  # Should not happen
        except ValueError, ex:
            eq_(msg, ex.args[0])

    # Test hashlib
    def test_hash_util_sha1(self):
        self.hash_file_calc(
            build_pack_utils.HashUtil({'cache-hash-algorithm': 'sha1'}),
            "cf6ef7e713aeff5426e592b8e897fed7590407af")

    def test_hash_util_sha256(self):
        self.hash_file_calc(
            build_pack_utils.HashUtil({'cache-hash-algorithm': 'sha256'}),
            "7cd9d6e1140dfbefecd88b7552ac6be5bf59885c604da3cf52ededb988e9fff0")

    def test_hash_util_sha512(self):
        self.hash_file_calc(
            build_pack_utils.HashUtil({'cache-hash-algorithm': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_hash_util_matches(self):
        self.hash_file_matches(
            build_pack_utils.HashUtil({'cache-hash-algorithm': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_hash_util_not_matches(self):
        self.hash_file_not_matches(
            build_pack_utils.HashUtil({'cache-hash-algorithm': 'sha512'}),
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_hash_util_no_file(self):
        hsh = build_pack_utils.HashUtil({'cache-hash-algorithm': '512'})
        assert '' == hsh.calculate_hash(None)
        assert '' == hsh.calculate_hash('')

    def test_hash_util_empty_algorithms(self):
        hsh = build_pack_utils.HashUtil({'cache-hash-algorithm': ''})
        self.hash_file_bad_algorithm(hsh, '', 'unsupported hash type')

    def test_hash_util_bad_algorithm(self):
        hsh = build_pack_utils.HashUtil({'cache-hash-algorithm': '???'})
        self.hash_file_bad_algorithm(hsh, '???', 'unsupported hash type')

    def test_hash_util_missing_algorithm(self):
        hsh = build_pack_utils.HashUtil({'cache-hash-algorithm': '2'})
        self.hash_file_bad_algorithm(hsh, '2', 'unsupported hash type')

    # Test External SHA
    def test_sha_hash_util_sha1(self):
        self.hash_file_calc(
            build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '1'}),
            "cf6ef7e713aeff5426e592b8e897fed7590407af")

    def test_sha_hash_util_sha256(self):
        self.hash_file_calc(
            build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '256'}),
            "7cd9d6e1140dfbefecd88b7552ac6be5bf59885c604da3cf52ededb988e9fff0")

    def test_sha_hash_util_sha512(self):
        self.hash_file_calc(
            build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_sha_hash_util_matches(self):
        self.hash_file_matches(
            build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_sha_hash_util_not_matches(self):
        self.hash_file_not_matches(
            build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '512'}),
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_sha_hash_util_no_file(self):
        hsh = build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '512'})
        assert '' == hsh.calculate_hash(None)
        assert '' == hsh.calculate_hash('')

    def test_sha_hash_util_empty_algorithms(self):
        hsh = build_pack_utils.ShaHashUtil({'cache-hash-algorithm': ''})
        self.hash_file_bad_algorithm(
            hsh, '', 'Value "" invalid for option a (number expected)')

    def test_sha_hash_util_bad_algorithm(self):
        hsh = build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '???'})
        self.hash_file_bad_algorithm(
            hsh, '???', 'Value "???" invalid for option a (number expected)')

    def test_sha_hash_util_missing_algorithm(self):
        hsh = build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '2'})
        self.hash_file_bad_algorithm(
            hsh, '2', 'shasum: Unrecognized algorithm')


class TestDirectoryCacheManager(object):

    def __init__(self):
        self._hshUtil = build_pack_utils.HashUtil(
            {'cache-hash-algorithm': 'sha256'})

    def tearDown(self):
        path = os.path.join(tempfile.gettempdir(), 'junk.txt')
        if os.path.exists(path):
            os.remove(path)
        path = os.path.join(tempfile.gettempdir(), 'DCM')
        if os.path.exists(path):
            shutil.rmtree(path)

    def create_junk_file(self, fileName):
        path = os.path.join(tempfile.gettempdir(), fileName)
        with open(path, 'w') as tmp:
            tmp.write("Hello World!")
        return (path, self._hshUtil.calculate_hash(path))

    @with_setup(teardown=tearDown)
    def test_basics(self):
        path = os.path.join(tempfile.gettempdir(), "DCM")
        dcm = build_pack_utils.DirectoryCacheManager({
            'file-cache-base-directory': path,
            'use-external-hash': False,
            'cache-hash-algorithm': 'sha256'})
        assert not dcm.exists('asdf', None)
        junk_file = self.create_junk_file('junk.txt')
        key = os.path.basename(junk_file[0])
        dcm.put(key, junk_file[0], junk_file[1])
        assert dcm.exists(key, junk_file[1])
        assert dcm.get(key, junk_file[1]).endswith('DCM/junk.txt')
        dcm.delete(key)
        assert not dcm.exists(key, junk_file[1])


class TestUnzipUtil(object):

    HASH_FILE = './test/data/HASH'
    HASH_FILE_ZIP = './test/data/HASH.zip'
    HASH_FILE_BZ2 = './test/data/HASH.bz2'
    HASH_FILE_GZ = './test/data/HASH.gz'
    HASH_FILE_TAR = './test/data/HASH.tar'
    HASH_FILE_TARGZ = './test/data/HASH.tar.gz'
    HASH_FILE_TARBZ2 = './test/data/HASH.tar.bz2'

    def __init__(self):
        self._hshUtil = build_pack_utils.HashUtil(
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
        uzUtil = build_pack_utils.UnzipUtil({})
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
        uzUtil = build_pack_utils.UnzipUtil({})
        outPath = uzUtil.extract(self.HASH_FILE_ZIP, self._dir)
        assert len(outPath) > 0
        assert outPath.startswith(self._dir)
        assert os.path.exists(self._path)
        assert self._hash == self._hshUtil.calculate_hash(self._path)

    def test_pick_based_on_file_extension(self):
        uzUtil = build_pack_utils.UnzipUtil({})
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


class TestCloudFoundryUtil(object):

    def setUp(self):
        self.old_sys_argv = sys.argv
        sys.argv = [
            '/tmp/buildpacks/my-buildpack/bin/compile',
            os.path.join(tempfile.gettempdir(), '/tmp/staged/app'),
            os.path.join(tempfile.gettempdir(), '/tmp/cache')]
        os.environ['MEMORY_LIMIT'] = '64m'
        os.environ['TMPDIR'] = '/tmp'

    def tearDown(self):
        path = os.path.join(tempfile.gettempdir(), '/tmp/staged/app')
        if os.path.exists(path):
            shutil.rmtree(path)
        path = os.path.join(tempfile.gettempdir(), '/tmp/cache')
        if os.path.exists(path):
            shutil.rmtree(path)
        sys.argv = self.old_sys_argv

    @with_setup(setup=setUp, teardown=tearDown)
    def test_load_env(self):
        cf = build_pack_utils.CloudFoundryUtil()
        assert '/tmp/staged/app' == cf.BUILD_DIR
        assert '/tmp/cache' == cf.CACHE_DIR
        assert '/tmp' == cf.TEMP_DIR
        assert '/tmp/buildpacks/my-buildpack' == cf.BP_DIR
        assert '64m' == cf.MEMORY_LIMIT
        assert os.path.exists(cf.BUILD_DIR)
        assert os.path.exists(cf.CACHE_DIR)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_load_json_config_file(self):
        cf = build_pack_utils.CloudFoundryUtil()
        cfg = cf.load_json_config_file('./test/data/config.json')
        assert cfg['int'] == 5
        assert cfg['string'] == '1234'
        assert len(cfg['list']) == 5
        assert cfg['list'][3] == 4
        assert 'y' in cfg['map'].keys()
        assert cfg['map']['z'] == 3

    @with_setup(setup=setUp, teardown=tearDown)
    def test_load_json_config_file_from(self):
        cf = build_pack_utils.CloudFoundryUtil()
        cfg = cf.load_json_config_file_from('./test/data/', 'config.json')
        assert cfg['int'] == 5
        assert cfg['string'] == '1234'
        assert len(cfg['list']) == 5
        assert cfg['list'][3] == 4
        assert 'y' in cfg['map'].keys()
        assert cfg['map']['z'] == 3


class TestCloudFoundryInstallerBinaries(object):
    def test_install_binary_cached(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(build_pack_utils.CloudFoundryInstaller)
        installer._cf = Dingus('cf',
                               BUILD_DIR='/tmp/build_dir',
                               CACHE_DIR='/tmp/cache_dir')
        installer._cfg = {
            'LOCAL_PACKAGE': 'tomcat.tar.gz',
            'LOCAL_PACKAGE_HASH': '1234WXYZ',
            'LOCAL_DOWNLOAD_PREFIX': 'PREFIX',
            'LOCAL_PACKAGE_INSTALL_DIR': '/tmp/packages'
        }
        installer._unzipUtil = Dingus('unzip')
        installer._hashUtil = Dingus('hash',
                                     calculate_hash__returns='1234WXYZ')
        installer._dcm = Dingus('dcm', get__returns=None)
        installer._dwn = Dingus('download')
        # Run test
        instDir = installer.install_binary('LOCAL')
        # Verify execution path, file is not cached
        # Cache manager checks for file
        assert installer._dcm.get.calls().once()
        assert None is installer._dcm.calls('get')[0].return_value
        # download is called once with file path
        assert installer._dwn.download.calls().once()
        assert 'PREFIX/tomcat.tar.gz' == \
            installer._dwn.calls('download')[0].args[0]
        # hash is called with file path
        assert installer._hashUtil.calculate_hash.calls().once()
        calls = installer._hashUtil.calls('calculate_hash')
        assert calls[0].args[0].endswith('tomcat.tar.gz')
        # cache manager is called with key and digest
        assert installer._dcm.put.calls().once()
        assert 'tomcat.tar.gz' == installer._dcm.calls('put')[0].args[0]
        assert '1234WXYZ' == installer._dcm.calls('put')[0].args[2]
        # file is extracted
        assert installer._unzipUtil.extract.calls().once()
        # verify installation directory
        eq_('/tmp/packages/tomcat', instDir)

    def test_install_binary_not_cached(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(build_pack_utils.CloudFoundryInstaller)
        installer._cf = Dingus('cf',
                               BUILD_DIR='/tmp/build_dir',
                               CACHE_DIR='/tmp/cache_dir')
        installer._cfg = {
            'LOCAL_PACKAGE': 'tomcat.tar.gz',
            'LOCAL_PACKAGE_HASH': '1234WXYZ',
            'LOCAL_DOWNLOAD_PREFIX': 'PREFIX',
        }
        installer._unzipUtil = Dingus('unzip')
        installer._hashUtil = Dingus('hash',
                                     calculate_hash__returns='1234WXYZ')
        installer._dcm = Dingus('dcm', get__returns='/tmp/cache/tomcat.tar.gz')
        installer._dwn = Dingus('download')
        # Run test
        instDir = installer.install_binary('LOCAL')
        # Verify execution path, file is not cached
        # Cache manager checks for file
        assert installer._dcm.get.calls().once()
        assert '/tmp/cache/tomcat.tar.gz' == \
            installer._dcm.calls('get')[0].return_value
        # make sure download section is skipped
        assert 0 == len(installer._dwn.calls('download'))
        assert 0 == len(installer._hashUtil.calls('calculate_hash'))
        assert 0 == len(installer._dcm.calls('put'))
        # file is extracted
        assert installer._unzipUtil.extract.calls().once()
        eq_('/tmp/build_dir/tomcat', instDir)


class TestCloudFoundryInstallerConfig(object):
    def setUp(self):
        self._tmpDir = tempfile.mkdtemp()

    def tearDown(self):
        if self._tmpDir:
            shutil.rmtree(self._tmpDir)

    def assertFileExistsAndDelete(self, filePath):
        assert os.path.exists(filePath)
        os.remove(filePath)
        assert not os.path.exists(filePath)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_install_from_build_pack(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(build_pack_utils.CloudFoundryInstaller)
        installer._cf = Dingus(
            'cf',
            BP_DIR='./test/data',
            BUILD_DIR=self._tmpDir)
        # Test copying files from build pack
        tmpConfig = os.path.join(self._tmpDir, 'config.json')
        # test with default toLocation
        installer.install_from_build_pack('config.json')
        self.assertFileExistsAndDelete(tmpConfig)
        # test when toLocation is same as default
        installer.install_from_build_pack('config.json', 'config.json')
        self.assertFileExistsAndDelete(tmpConfig)
        # test when toLocation is different
        installer.install_from_build_pack('config.json', 'renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'renamed.json'))
        # test when toLocation is nested path
        installer.install_from_build_pack('config.json',
                                          'in/a/path/renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'in/a/path/renamed.json'))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_install_from_app(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(build_pack_utils.CloudFoundryInstaller)
        installer._cf = Dingus(
            'cf',
            BP_DIR='./test/data',
            BUILD_DIR=self._tmpDir)
        # Add file to temp dir
        installer.install_from_build_pack('config.json')
        # Test copying files from app
        installer.install_from_application('config.json', 'renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'renamed.json'))
        # Test with nested path
        installer.install_from_application(
            'config.json', 'in/a/path/renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'in/a/path/renamed.json'))

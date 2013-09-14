import build_pack_utils
import urllib2
import os.path
import tempfile
from nose.tools import *

class TestDownloaderUtils(object):
    def _run_download(self, dwn, url):
        path = os.path.join(tempfile.gettempdir(), 'KEYS')
        dwn.download(url, path)
        assert os.path.exists(path)
        with open(path, 'rt') as keysFile:
            assert 11 == keysFile.read().count('-----END PGP PUBLIC KEY BLOCK-----')

    def run_download(self, dwn):
        self._run_download(dwn, 'http://archive.apache.org/dist/tomcat/tomcat-8/KEYS')

    def run_download_404(self, dwn):
        self._run_download(dwn, 'http://www.mikusa.com/does_not_exist')

    # Tests start here
    def test_downloader(self):
        self.run_download(build_pack_utils.Downloader({}))
    
    def test_downloader(self):
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
        with assert_raises(ValueError) as cm:
            hsh.calculate_hash(self.HASH_FILE)
        eq_(msg, cm.exception.message)

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
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53" \
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_hash_util_matches(self):
        self.hash_file_matches(
            build_pack_utils.HashUtil({'cache-hash-algorithm': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53" \
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
        self.hash_file_bad_algorithm(hsh, '', 'unsupported hash type ')

    def test_hash_util_bad_algorithm(self):
        hsh = build_pack_utils.HashUtil({'cache-hash-algorithm': '???'})
        self.hash_file_bad_algorithm(hsh, '???', 'unsupported hash type ???')

    def test_hash_util_missing_algorithm(self):
        hsh = build_pack_utils.HashUtil({'cache-hash-algorithm': '2'})
        self.hash_file_bad_algorithm(hsh, '2', 'unsupported hash type 2')

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
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53" \
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_sha_hash_util_matches(self):
        self.hash_file_matches(
            build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53" \
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
        self.hash_file_bad_algorithm(hsh, '',
                'Value "" invalid for option a (number expected)')

    def test_sha_hash_util_bad_algorithm(self):
        hsh = build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '???'})
        self.hash_file_bad_algorithm(hsh, '???',
                'Value "???" invalid for option a (number expected)')

    def test_sha_hash_util_missing_algorithm(self):
        hsh = build_pack_utils.ShaHashUtil({'cache-hash-algorithm': '2'})
        self.hash_file_bad_algorithm(hsh, '2', 'shasum: Unrecognized algorithm')


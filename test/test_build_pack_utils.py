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


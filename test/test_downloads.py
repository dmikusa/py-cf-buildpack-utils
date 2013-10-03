import os
import tempfile
import urllib2
from nose.tools import raises
from build_pack_utils import Downloader
from build_pack_utils import CurlDownloader


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
        self.run_download(Downloader({}))

    def test_downloader_verbose(self):
        self.run_download(Downloader({'verbose': True}))

    @raises(urllib2.HTTPError)
    def test_downloader_404(self):
        self.run_download_404(Downloader({}))

    def test_curl_downloader(self):
        self.run_download(CurlDownloader({}))

    @raises(RuntimeError)
    def test_curl_downloader_404(self):
        self.run_download_404(CurlDownloader({}))

import os
import tempfile
import urllib2
from nose.tools import raises
from nose.tools import eq_
from build_pack_utils import Downloader
from build_pack_utils import CurlDownloader


class TestDownloaderUtils(object):
    def _run_download(self, dwn, url):
        path = os.path.join(tempfile.gettempdir(), 'KEYS')
        dwn.download(url, path)
        eq_(True, os.path.exists(path))
        with open(path, 'rt') as keysFile:
            eq_(11,
                keysFile.read().count('-----END PGP PUBLIC KEY BLOCK-----'))

    def run_download(self, dwn):
        self._run_download(
            dwn,
            'http://archive.apache.org/dist/tomcat/tomcat-8/KEYS')

    def run_download_404(self, dwn):
        self._run_download(dwn, 'http://www.mikusa.com/does_not_exist')

    def run_download_direct(self, dwn):
        return dwn.download_direct(
            'http://archive.apache.org/dist/tomcat/tomcat-8/KEYS')

    # Tests start here
    def test_downloader(self):
        self.run_download(Downloader({}))

    @raises(urllib2.HTTPError)
    def test_downloader_404(self):
        self.run_download_404(Downloader({}))

    def test_curl_downloader(self):
        self.run_download(CurlDownloader({}))

    @raises(RuntimeError)
    def test_curl_downloader_404(self):
        self.run_download_404(CurlDownloader({}))

    def test_download_direct(self):
        data = self.run_download_direct(Downloader({}))
        eq_(11, data.count('-----BEGIN PGP PUBLIC KEY BLOCK-----'))
    
    def test_download_direct_curl(self):
        data = self.run_download_direct(CurlDownloader({}))
        eq_(11, data.count('-----BEGIN PGP PUBLIC KEY BLOCK-----'))

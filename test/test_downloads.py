import os
import tempfile
import urllib2
from nose.tools import raises
from nose.tools import eq_
from build_pack_utils import Downloader
from build_pack_utils import CurlDownloader


class TestDownloaderUtils(object):
    def setUp(self):
        self.downloadFile = os.path.join(tempfile.gettempdir(),
                                         'introduction.html')

    def tearDown(self):
        if os.path.exists(self.downloadFile):
            os.remove(self.downloadFile)

    def _run_download(self, dwn, url):
        dwn.download(url, self.downloadFile)
        eq_(True, os.path.exists(self.downloadFile))
        with open(self.downloadFile, 'rt') as keysFile:
            eq_(1, keysFile.read().count('PEP 249'))

    def run_download(self, dwn):
        self._run_download(
            dwn,
            'http://www.mikusa.com/python-mysql-docs/introduction.html')

    def run_download_404(self, dwn):
        self._run_download(dwn, 'http://www.mikusa.com/does_not_exist')

    def run_download_direct(self, dwn):
        return dwn.download_direct(
            'http://www.mikusa.com/python-mysql-docs/introduction.html')

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
        eq_(1, data.count('PEP 249'))

    def test_download_direct_curl(self):
        data = self.run_download_direct(CurlDownloader({}))
        eq_(1, data.count('PEP 249'))

#    def test_with_proxy(self):
#        # disabled by default, as it requires a proxy server in place
#        self.run_download(
#            Downloader({'http_proxy': 'http://localhost:8080/'}))

#    def test_with_proxy_auth(self):
#        # disabled by default, as it requires a proxy server w/auth in place
#        self.run_download(
#            Downloader({'http_proxy': 'http://dan:dan@localhost:8080/'}))

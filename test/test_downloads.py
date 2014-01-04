import os
import tempfile
import urllib2
from nose.tools import raises
from nose.tools import eq_
from build_pack_utils import Downloader
from build_pack_utils import CurlDownloader


class TestDownloaderUtils(object):
    def _run_download(self, dwn, url):
        path = os.path.join(tempfile.gettempdir(), 'introduction.html')
        dwn.download(url, path)
        eq_(True, os.path.exists(path))
        with open(path, 'rt') as keysFile:
            eq_(1, keysFile.read().count('PEP 249'))

    def run_download(self, dwn):
        self._run_download(
            dwn,
            'http://www.mikusa.com/python-mysql-docs/introduction.html')

    def run_download_format(self, dwn):
        self._run_download(
            dwn,
            '{BASE}/{FILE}')

    def run_download_404(self, dwn):
        self._run_download(dwn, 'http://www.mikusa.com/does_not_exist')

    def run_download_direct(self, dwn):
        return dwn.download_direct(
            'http://www.mikusa.com/python-mysql-docs/introduction.html')

    def run_download_direct_format(self, dwn):
        return dwn.download_direct('{BASE}/{FILE}')

    # Tests start here
    def test_downloader(self):
        self.run_download(Downloader({}))

    def test_downloader_format(self):
        self.run_download_format(
            Downloader({'BASE': 'http://www.mikusa.com/python-mysql-docs/',
                        'FILE': 'introduction.html'}))

    @raises(urllib2.HTTPError)
    def test_downloader_404(self):
        self.run_download_404(Downloader({}))

    def test_curl_downloader(self):
        self.run_download(CurlDownloader({}))

    def test_curl_downloader_format(self):
        self.run_download_format(
            CurlDownloader({'BASE': 'http://www.mikusa.com/python-mysql-docs/',
                            'FILE': 'introduction.html'}))

    @raises(RuntimeError)
    def test_curl_downloader_404(self):
        self.run_download_404(CurlDownloader({}))

    def test_download_direct(self):
        data = self.run_download_direct(Downloader({}))
        eq_(1, data.count('PEP 249'))

    def test_download_direct_format(self):
        data = self.run_download_direct_format(
            Downloader({'BASE': 'http://www.mikusa.com/python-mysql-docs/',
                        'FILE': 'introduction.html'}))
        eq_(1, data.count('PEP 249'))

    def test_download_direct_curl(self):
        data = self.run_download_direct(CurlDownloader({}))
        eq_(1, data.count('PEP 249'))

    def test_download_direct_format_curl(self):
        data = self.run_download_direct_format(
            CurlDownloader({'BASE': 'http://www.mikusa.com/python-mysql-docs/',
                            'FILE': 'introduction.html'}))
        eq_(1, data.count('PEP 249'))

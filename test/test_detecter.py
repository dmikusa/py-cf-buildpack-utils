from nose.tools import eq_
from build_pack_utils import BaseFileSearch
from build_pack_utils import TextFileSearch
from build_pack_utils import RegexFileSearch
from build_pack_utils import StartsWithFileSearch
from build_pack_utils import EndsWithFileSearch
from build_pack_utils import ContainsFileSearch


class TestBaseFileSearch(object):
    def setUp(self):
        self.files = []

    def match_stub(self, term):
        self.files.append(term)
        return False

    def test_search(self):
        bfs = BaseFileSearch()
        bfs._match = self.match_stub
        bfs.search('./test/data')
        eq_(23, len(self.files))
        assert '.bp-config' in self.files
        assert 'defaults' in self.files
        assert 'HASH' in self.files
        assert 'HASH.zip' in self.files

    def test_search_with_full_path(self):
        bfs = BaseFileSearch()
        bfs.fullPath = True
        bfs._match = self.match_stub
        bfs.search('./test/data')
        eq_(23, len(self.files))
        assert './test/data/.bp-config' in self.files
        assert './test/data/defaults' in self.files
        assert './test/data/HASH' in self.files
        assert './test/data/HASH.zip' in self.files

    def test_search_recursive(self):
        bfs = BaseFileSearch()
        bfs.recursive = True
        bfs._match = self.match_stub
        bfs.search('./test/data')
        eq_(55, len(self.files))
        assert '.bp-config' in self.files
        assert 'defaults' in self.files
        assert 'HASH' in self.files
        assert 'HASH.zip' in self.files
        eq_(3, len([f for f in self.files if f == 'options.json']))

    def test_search_recursive_with_full_path(self):
        bfs = BaseFileSearch()
        bfs.fullPath = True
        bfs.recursive = True
        bfs._match = self.match_stub
        bfs.search('./test/data')
        eq_(55, len(self.files))
        assert './test/data/.bp-config' in self.files
        assert './test/data/defaults' in self.files
        assert './test/data/HASH' in self.files
        assert './test/data/HASH.zip' in self.files
        assert './test/data/options.json' in self.files
        assert './test/data/.bp-config/options.json' in self.files
        assert './test/data/defaults/options.json' in self.files


class TestMatchers(object):
    def test_text_match(self):
        tfs = TextFileSearch('junk')
        assert tfs._match('junk')
        assert not tfs._match('asdf')

    def test_regex_match(self):
        rfs = RegexFileSearch('^.*\.php$')
        assert rfs._match('index.php')
        assert not rfs._match('index.html')

    def test_starts_with_match(self):
        swfs = StartsWithFileSearch('index')
        assert swfs._match('index.php')
        assert not swfs._match('home.php')

    def test_ends_with_match(self):
        ewfs = EndsWithFileSearch('.php')
        assert ewfs._match('index.php')
        assert not ewfs._match('index.html')

    def test_contains_match(self):
        cfs = ContainsFileSearch('index')
        assert cfs._match('index.php')
        assert cfs._match('junk-index')
        assert cfs._match('junk-index-junk')
        assert not cfs._match('junk-junk')

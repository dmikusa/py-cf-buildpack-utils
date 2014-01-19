import os
import shutil
import tempfile
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils


class TestCopytree(object):
    def setUp(self):
        self.toDir = tempfile.mkdtemp(prefix='copytree-')

    def tearDown(self):
        if os.path.exists(self.toDir):
            shutil.rmtree(self.toDir)

    def assert_exists(self, path):
        eq_(True, os.path.exists(os.path.join(self.toDir, path)))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_copytree_dirs(self):
        fromDir = 'test/data/plugins'
        utils.copytree(fromDir, self.toDir)
        self.assert_exists(self.toDir)
        self.assert_exists(os.path.join(self.toDir, 'test1'))
        self.assert_exists(os.path.join(self.toDir, 'test2'))
        self.assert_exists(os.path.join(self.toDir, 'test3'))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_copytree_flat(self):
        fromDir = 'test/data/config'
        utils.copytree(fromDir, self.toDir)
        self.assert_exists(self.toDir)
        self.assert_exists(os.path.join(self.toDir, 'options.json'))
        self.assert_exists(os.path.join(self.toDir, 'junk.xml'))


class TestFormattedDict(object):
    def test_empty(self):
        x = utils.FormattedDict()
        eq_(0, len(x.keys()))

    def test_basics(self):
        x = utils.FormattedDict({
            'A': 1234,
            'B': 5678
        })
        eq_(1234, x['A'])
        eq_(5678, x['B'])
        eq_(1234, x.get('A'))
        eq_(5678, x.get('B'))
        eq_(None, x.get('C'))
        eq_(0, x.get('C', 0))

    def test_kwargs(self):
        x = utils.FormattedDict(A=1234, B=5678)
        eq_(1234, x['A'])
        eq_(5678, x['B'])
        eq_(1234, x.get('A'))
        eq_(5678, x.get('B'))
        eq_(None, x.get('C'))
        eq_(0, x.get('C', 0))

    def test_formatted(self):
        x = utils.FormattedDict(A=1234, B=5678, C='{A}')
        eq_('1234', x['C'])
        eq_('1234', x.get('C'))

    def test_complicated(self):
        x = utils.FormattedDict({
            'A': 1234,
            'B': 5678,
            'C': '{A}/{B}',
            'D': '{C}/{B}',
            'E': '{D}/{C}'
        })
        eq_(1234, x['A'])
        eq_(5678, x['B'])
        eq_('1234/5678', x['C'])
        eq_('1234/5678/5678', x['D'])
        eq_('1234/5678', x.get('C'))
        eq_('1234/5678/5678', x.get('D'))
        eq_('1234/5678', x.get('C', None))
        eq_('1234/5678/5678', x.get('D', None))
        eq_('1234/5678/5678/1234/5678', x['E'])
        eq_('1234/5678/5678/1234/5678', x.get('E'))
        eq_('1234/5678/5678/1234/5678', x.get('E', None))
        eq_(None, x.get('F', None))

    def test_plain(self):
        x = utils.FormattedDict({
            'A': 1234,
            'B': 5678,
            'C': '{A}/{B}',
            'D': '{C}/{B}',
            'E': '{D}/{C}'
        })
        eq_(1234, x.get('A', format=False))
        eq_(5678, x.get('B', format=False))
        eq_('{A}/{B}', x.get('C', format=False))
        eq_('1234/5678', x.get('C', format=True))

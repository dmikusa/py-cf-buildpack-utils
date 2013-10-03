import os
from nose.tools import eq_
from build_pack_utils import Runner
from build_pack_utils import Builder
from build_pack_utils import CloudFoundryUtil
from build_pack_utils import api_method


class TestRunner(object):
    # these tests will fai on Windows, requires "ls" command

    def test_run_from_directory(self):
        cwd = os.getcwd()
        (retcode, stdout, stderr) = \
            Runner.run_from_directory(
                './test/data/', 'ls', ['-la'], shell=True)
        eq_(stderr, '')
        eq_(stdout, 'HASH\nHASH.bz2\nHASH.gz\nHASH.tar\nHASH.tar.bz2\n'
                    'HASH.tar.gz\nHASH.zip\nconfig.json\noptions.json\n')
        eq_(retcode, 0)
        eq_(cwd, os.getcwd())

    def test_run_from_directory_error(self):
        cwd = os.getcwd()
        (retcode, stdout, stderr) = \
            Runner.run_from_directory(
                './test/data/', 'ls', ['-la', '/doesnt/exist'], shell=False)
        eq_(stderr, 'ls: /doesnt/exist: No such file or directory\n')
        eq_(stdout, '')
        eq_(retcode, 1)
        eq_(cwd, os.getcwd())

    def test_run_from_directory_that_doesnt_exist(self):
        assert None is \
            Runner.run_from_directory(
                '/doesnt/exist', 'ls', ['-la'], shell=False)
        assert None is \
            Runner.run_from_directory(
                '/doesnt/exist', 'ls', ['-la'], shell=True)


class TestBuilderMerge(object):
    def __init__(self):
        # Do this to skip the constructor, not needed
        self.bpw = object.__new__(Builder)

    def test_merge_one_dict(self):
        res = self.bpw.merge({1: '123', 2: '456'})
        assert len(res) == 2
        assert 1 in res.keys()
        assert 2 in res.keys()
        assert '123' == res[1]
        assert '456' == res[2]

    def test_merge_two_dicts(self):
        res = self.bpw.merge({1: '123', 2: '456'},
                             {3: '789', 4: '0123'})
        assert len(res) == 4
        assert 1 in res.keys()
        assert 2 in res.keys()
        assert 3 in res.keys()
        assert 4 in res.keys()
        assert '123' == res[1]
        assert '456' == res[2]
        assert '789' == res[3]
        assert '0123' == res[4]

    def test_merge_three_dict(self):
        res = self.bpw.merge({1: '123', 2: '456'},
                             {3: '789', 4: '0123'},
                             {5: '4567', 6: '8901'})
        assert len(res) == 6
        assert 1 in res.keys()
        assert 2 in res.keys()
        assert 3 in res.keys()
        assert 4 in res.keys()
        assert 5 in res.keys()
        assert 6 in res.keys()
        assert '123' == res[1]
        assert '456' == res[2]
        assert '789' == res[3]
        assert '0123' == res[4]
        assert '4567' == res[5]
        assert '8901' == res[6]

    def test_merge_two_dicts_with_overlap(self):
        res = self.bpw.merge({1: '123', 2: '456'},
                             {2: '789', 3: '0123'})
        assert len(res) == 3
        assert 1 in res.keys()
        assert 2 in res.keys()
        assert 3 in res.keys()
        assert '123' == res[1]
        assert '789' == res[2]
        assert '0123' == res[3]


class TestBuilderConfig(object):
    def __init__(self):
        # Do this to skip the constructor, not needed
        self.bpw = object.__new__(Builder)
        self.bpw.cf = object.__new__(CloudFoundryUtil)

    def test_user_config_default(self):
        self.bpw.cf.BUILD_DIR = './test/data/'
        self.bpw.cfg = {}
        res = self.bpw.user_config()
        assert len(res) == 4
        assert "int" in res.keys()
        assert res['int'] == 5

    def test_user_config_manual(self):
        self.bpw.cfg = {
            'DEFAULT_USER_CONFIG_PATH': 'options.json'
        }
        self.bpw.cf.BUILD_DIR = './test/data/'
        res = self.bpw.user_config()
        assert len(res) == 4
        assert "int" in res.keys()
        assert res['int'] == 3

    def test_bp_config_default(self):
        self.bpw.cf.BP_DIR = './test/data/'
        self.bpw.cfg = {}
        res = self.bpw.default_config()
        assert len(res) == 4
        assert "int" in res.keys()
        assert res['int'] == 3

    def test_bp_config_manual(self):
        self.bpw.cfg = {
            'DEFAULT_CONFIG_PATH': 'config.json'
        }
        self.bpw.cf.BP_DIR = './test/data/'
        res = self.bpw.default_config()
        assert len(res) == 4
        assert "int" in res.keys()
        assert res['int'] == 5

    def test_use_config(self):
        self.bpw.cfg = None
        self.bpw.use({'x': '1234'})
        assert self.bpw.cfg is not None
        assert 'x' in self.bpw.cfg.keys()
        assert '1234' == self.bpw.cfg['x']
        instId = id(self.bpw.installer)
        self.bpw.use({'y': '4321'})
        assert 'y' in self.bpw.cfg.keys()
        assert '4321' == self.bpw.cfg['y']
        assert instId != id(self.bpw.installer)

#
# Builder().
#    use().
#        .default_config()
#        .user_config('path')
#

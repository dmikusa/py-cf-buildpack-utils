import os
from nose.tools import eq_
from build_pack_utils import CloudFoundryRunner


class TestCloudFoundryRunner(object):
    # these tests will fai on Windows, requires "ls" command

    def test_run_from_directory(self):
        cwd = os.getcwd()
        (retcode, stdout, stderr) = \
            CloudFoundryRunner.run_from_directory(
                './test/data/', 'ls', ['-la'], shell=True)
        eq_(stderr, '')
        eq_(stdout, 'HASH\nHASH.bz2\nHASH.gz\nHASH.tar\nHASH.tar.bz2\n'
                    'HASH.tar.gz\nHASH.zip\nconfig.json\n')
        eq_(retcode, 0)
        eq_(cwd, os.getcwd())

    def test_run_from_directory_error(self):
        cwd = os.getcwd()
        (retcode, stdout, stderr) = \
            CloudFoundryRunner.run_from_directory(
                './test/data/', 'ls', ['-la', '/doesnt/exist'], shell=False)
        eq_(stderr, 'ls: /doesnt/exist: No such file or directory\n')
        eq_(stdout, '')
        eq_(retcode, 1)
        eq_(cwd, os.getcwd())

    def test_run_from_directory_that_doesnt_exist(self):
        assert None is \
            CloudFoundryRunner.run_from_directory(
                '/doesnt/exist', 'ls', ['-la'], shell=False)
        assert None is \
            CloudFoundryRunner.run_from_directory(
                '/doesnt/exist', 'ls', ['-la'], shell=True)

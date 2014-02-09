import sys
import StringIO
from nose.tools import with_setup
from nose.tools import eq_
from build_pack_utils import Process
from build_pack_utils import ProcessManager


class TestProcess(object):
    def test_process(self):
        p = Process('ls -l')
        eq_(None, p.name)
        eq_(False, p.quiet)
        eq_(None, p.reader)
        eq_(None, p.printer)
        eq_(False, p.dead)
        (stdout, stderr) = p.communicate()
        eq_(True, stdout.find('README') > -1)
        eq_(None, stderr)

    def test_process_with_args(self):
        p = Process('ls -l', name='ls', quiet=True)
        eq_('ls (quiet)', p.name)
        eq_(True, p.quiet)
        eq_(None, p.reader)
        eq_(None, p.printer)
        eq_(False, p.dead)
        (stdout, stderr) = p.communicate()
        eq_(True, stdout.find('README') > -1)
        eq_(None, stderr)


class TestProcessManager(object):
    def setUp(self):
        self._orig_stdout = sys.stdout
        self._tmp_stdout = StringIO.StringIO()
        sys.stdout = self._tmp_stdout

    def tearDown(self):
        sys.stdout = self._orig_stdout

    @with_setup(setup=setUp, teardown=tearDown)
    def test_process_manager(self):
        pm = ProcessManager()
        pm.add_process('ls', 'ls -l')
        pm.loop()
        output = self._tmp_stdout.getvalue()
        eq_(True, output.find('README') > -1)
        eq_(True, output.find('setup.py') > -1)
        eq_(True, output.find('src') > -1)

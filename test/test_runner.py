import os
import os.path
import sys
import tempfile
import shutil
import cStringIO
from nose.tools import eq_
from build_pack_utils import runner


TEST_BP = 'https://github.com/dmikusa-pivotal/cf-test-buildpack'
TEST_APP = 'test/data/app'


class TestRunner(object):
    def __init__(self):
        self._cwd = os.getcwd()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='bp-test')
        self.ctx = {
            'BUILD_DIR': os.path.join(self.root, 'build'),
            'CACHE_DIR': os.path.join(self.root, 'cache')
        }
        os.chdir(self._cwd)
        shutil.copytree(TEST_APP, self.ctx['BUILD_DIR'])
        self.buf = cStringIO.StringIO()
        self.bp = runner.BuildPack(self.ctx, TEST_BP, stream=self.buf)

    def tearDown(self):
        if os.path.exists(self.root):
            shutil.rmtree(self.root)
        if os.path.exists(self.bp.bp_dir):
            shutil.rmtree(self.bp.bp_dir)

    def test_clone(self):
        self.bp._clone()
        eq_(True, os.path.exists(self.bp.bp_dir))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir, 'bin')))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir,
                                              'bin', 'compile')))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir,
                                              'bin', 'release')))
        eq_(True, os.path.exists(os.path.join(self.bp.bp_dir,
                                              'bin', 'detect')))

    def test_detect(self):
        self.bp._clone()
        res = self.bp._detect()
        eq_('CACHETEST', res)

    def test_detect_fail(self):
        self.bp._clone()
        os.remove(os.path.join(self.ctx['BUILD_DIR'], 'cache-test.txt'))
        try:
            self.bp._detect()
            assert "Should Fail!", False
        except Exception, e:
            eq_(155, str(e).find('returned non-zero exit status 1'))
            eq_('no\n', e.output)

    def test_compile(self):
        self.bp._clone()
        self.bp._compile()
        output = self.buf.getvalue()
        eq_(True, output.find('Running cache test...') >= 0)
        eq_(True, output.find('Listing Environment:') >= 0)
        eq_(True, output.find('CPU Info') >= 0)

    def test_release(self):
        self.bp._clone()
        output = self.bp._release()
        eq_(True, output.startswith('---'))
        eq_(True, output.find('web: ./start.sh') >= 0)

    def test_run(self):
        self.bp.run()


class TestStreamOutput(object):
    def setUp(self):
        self.string_stream = cStringIO.StringIO()
        (self.file_no,
         self.file_name) = tempfile.mkstemp(prefix='stream-test',
                                            suffix='.txt')
        self.file_stream = os.fdopen(self.file_no)

    def tearDown(self):
        self.file_stream.close()
        os.remove(self.file_name)

    def test_stream_echo(self):
        runner.stream_output(self.file_stream, ['echo', 'Hello World!'])
        self.file_stream.seek(0)
        eq_("Hello World!\n", self.file_stream.read())

    def test_stream_echo_stdout(self):
        runner.stream_output(sys.stdout, ['echo', 'Hello World!'])

    def test_stream_echo_string(self):
        runner.stream_output(self.string_stream, ['echo', 'Hello World!'])
        self.string_stream.seek(0)
        eq_("Hello World!\n", self.string_stream.read())

    def test_stream_big_file(self):
        # https://blog.nelhage.com/2010/02/a-very-subtle-bug/
        #  fixed in Python 3, it appears
        def fix_pipe():
            import signal
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        size = 625000  # 5MB
        runner.stream_output(self.file_stream,
                             "cat /dev/urandom | head -c 625000",
                             shell=True,
                             preexec_fn=fix_pipe)
        self.file_stream.seek(0)
        eq_(size, os.path.getsize(self.file_name))

    def test_stream_big_string(self):
        # https://blog.nelhage.com/2010/02/a-very-subtle-bug/
        #  fixed in Python 3, it appears
        def fix_pipe():
            import signal
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        size = 625000  # 5MB
        runner.stream_output(self.string_stream,
                             "cat /dev/urandom | head -c 625000",
                             shell=True,
                             preexec_fn=fix_pipe)
        self.string_stream.seek(0)
        eq_(size, len(self.string_stream.read()))

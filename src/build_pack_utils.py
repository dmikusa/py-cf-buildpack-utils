import os
import os.path
import urllib2
import hashlib
import shutil
from functools import partial
from subprocess import Popen
from subprocess import PIPE

class Downloader(object):

    def __init__(self, config):
        self._cfg = config

    def download(self, url, toFile):
        res = urllib2.urlopen(url)
        with open(toFile, 'w') as f:
            f.write(res.read())
        if self._cfg.get('verbose', False):
            print 'Downloaded [%s] to [%s]' % (url, toFile)


class CurlDownloader(object):

    def __init__(self, config):
        self._cfg = config

    def download(self, url, toFile):
        proc = Popen(["curl", "-s", 
                      "-o", toFile, 
                      "-w", '%{http_code}',
                      url], stdout=PIPE)
        output, unused_err = proc.communicate()
        retcode = proc.poll()
        if output and \
                (output.startswith('4') or 
                 output.startswith('5')):
            raise RuntimeError("curl says [%s]" % output)


class BaseCacheManager(object):

    def __init__(self, config):
        if config['use-external-hash']:
            self._hashUtil = ShaHashUtil(config)
        else:
            self._hashUtil = HashUtil(config)

    def get(self, key, digest):
        return None

    def put(self, key, fileToCache):
        pass

    def delete(self, key):
        pass

    def exists(self, key, digest):
        return False


class DirectoryCacheManager(BaseCacheManager):

    def __init__(self, config):
        BaseCacheManager.__init__(self, config)
        self._baseDir = config['file-cache-base-directory']
        if not os.path.exists(self._baseDir):
            os.makedirs(self._baseDir)

    def get(self, key, digest):
        path = os.path.join(self._baseDir, key)
        if self.exists(key, digest):
            return path

    def put(self, key, fileToCache, digest):
        path = os.path.join(self._baseDir, key)
        if (os.path.exists(path) and
                not self._hashUtil.does_hash_match(digest, path)):
            print "File already exists in the cache, but the digest " \
                    "does not match.  Will update the cache if the " \
                    "underlying file system supports it."
        shutil.copy(fileToCache, path)

    def delete(self, key):
        path = os.path.join(self._baseDir, key)
        if os.path.exists(path):
            print "You are trying to delete a file from the cache " \
                    "this is not supported for all file systems."
        os.remove(path)

    def exists(self, key, digest):
        path = os.path.join(self._baseDir, key)
        return (os.path.exists(path) and
                self._hashUtil.does_hash_match(digest, path))


class HashUtil(object):

    def __init__(self, config):
        self._cfg = config

    def calculate_hash(self, checkFile):
        if checkFile is None or checkFile == '':
            return ''
        hsh = hashlib.new(self._cfg['cache-hash-algorithm'])
        with open(checkFile, 'rb') as fileIn:
            for buf in iter(partial(fileIn.read, 8196), ''):
                hsh.update(buf)
        return hsh.hexdigest()

    def does_hash_match(self, digest, toFile):
        return (digest == self.calculate_hash(toFile))


class ShaHashUtil(HashUtil):

    def __init__(self, config):
        HashUtil.__init__(self, config)

    def calculate_hash(self, checkFile):
        if checkFile is None or checkFile == '':
            return ''
        proc = Popen(["shasum", "-b",
                      "-a", self._cfg['cache-hash-algorithm'],
                      checkFile], stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate()
        retcode = proc.poll()
        if retcode == 0:
            return output.strip().split(' ')[0]
        elif retcode == 1:
            raise ValueError(err.split('\n')[0])



import sys
import os
import os.path
import urllib2
import json
import hashlib
import shutil
import gzip
import bz2
import tarfile
import zipfile
import tempfile
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
        proc.poll()
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


class UnzipUtil(object):

    def __init__(self, config):
        self._cfg = config

    def _unzip(self, zipFile, intoDir):
        try:
            zipIn = zipfile.ZipFile(zipFile, 'r')
            zipIn.extractall(intoDir)
        finally:
            if zipIn:
                zipIn.close()
        return intoDir

    def _untar(self, zipFile, intoDir):
        try:
            tarIn = tarfile.open(zipFile, 'r:')
            tarIn.extractall(intoDir)
        finally:
            if tarIn:
                tarIn.close()
        return intoDir

    def _gunzip(self, zipFile, intoDir):
        path = os.path.join(intoDir, os.path.basename(zipFile)[:-3])
        try:
            zipIn = gzip.open(zipFile, 'rb')
            with open(path, 'wb') as zipOut:
                for buf in iter(partial(zipIn.read, 8196), ''):
                    zipOut.write(buf)
        finally:
            if zipIn:
                zipIn.close()
        return path

    def _bunzip2(self, zipFile, intoDir):
        path = os.path.join(intoDir, os.path.basename(zipFile)[:-4])
        try:
            zipIn = bz2.BZ2File(zipFile, 'rb')
            with open(path, 'wb') as zipOut:
                for buf in iter(partial(zipIn.read, 8196), ''):
                    zipOut.write(buf)
        finally:
            if zipIn:
                zipIn.close()
        return path

    def _tar_gunzip(self, zipFile, intoDir):
        try:
            tarIn = tarfile.open(zipFile, 'r:gz')
            tarIn.extractall(intoDir)
        finally:
            if tarIn:
                tarIn.close()
        return intoDir

    def _tar_bunzip2(self, zipFile, intoDir):
        try:
            tarIn = tarfile.open(zipFile, 'r:bz2')
            tarIn.extractall(intoDir)
        finally:
            if tarIn:
                tarIn.close()
        return intoDir

    def _pick_based_on_file_extension(self, zipFile):
        if zipFile.endswith('.tar.gz') or zipFile.endswith('.tgz'):
            return self._tar_gunzip
        if zipFile.endswith('.tar.bz2'):
            return self._tar_bunzip2
        if zipFile.endswith('.tar'):
            return self._untar
        if zipFile.endswith('.gz'):
            return self._gunzip
        if zipFile.endswith('.bz2'):
            return self._bunzip2
        if zipFile.endswith('.zip') and zipfile.is_zipfile(zipFile):
            return self._unzip

    def extract(self, zipFile, intoDir, method=None):
        if not method:
            method = self._pick_based_on_file_extension(zipFile)
        return method(zipFile, intoDir)


class CloudFoundryUtil(object):
    def __init__(self):
        # Open stdout unbuffered
        if hasattr(sys.stdout, 'fileno'):
            sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
        # User's Application Files, build droplet here
        self.BUILD_DIR = (len(sys.argv) >= 2) and sys.argv[1] or None
        # Cache space for the build pack
        self.CACHE_DIR = (len(sys.argv) >= 3) and sys.argv[2] or None
        # Temp space
        self.TEMP_DIR = os.environ.get('TMPDIR', tempfile.gettempdir())
        # Build Pack Location
        self.BP_DIR = os.path.dirname(os.path.dirname(sys.argv[0]))
        # Memory Limit
        self.MEMORY_LIMIT = os.environ.get('MEMORY_LIMIT', None)
        # Make sure cache & build directories exist
        if not os.path.exists(self.BUILD_DIR):
            os.makedirs(self.BUILD_DIR)
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)

    def load_json_config_file_from(self, folder, cfgFile):
        return self.load_json_config_file(os.path.join(folder, cfgFile))

    def load_json_config_file(self, cfgPath):
        if os.path.exists(cfgPath):
            with open(cfgPath, 'rt') as cfgFile:
                return json.load(cfgFile)


class CloudFoundryInstaller(object):
    def __init__(self, cf, cfg):
        self._cf = cf
        self._cfg = cfg
        self._unzipUtil = UnzipUtil(cfg)
        self._hashUtil = HashUtil(cfg)
        self._dcm = DirectoryCacheManager(cfg)
        self._dwn = Downloader(cfg)

    @staticmethod
    def _safe_makedirs(path):
        try:
            os.makedirs(path)
        except OSError, e:
            # Ignore if it exists
            if e.errno != 17:
                raise e

    def install_binary(self, installKey):
        fileName = self._cfg['%s_PACKAGE' % installKey]
        digest = self._cfg['%s_PACKAGE_HASH' % installKey]
        # check cache & compare digest
        # use cached file or download new
        # download based on cfg settings
        fileToInstall = self._dcm.get(fileName, digest)
        if fileToInstall is None:
            fileToInstall = os.path.join(self._cf.CACHE_DIR, fileName)
            self._dwn.download(
                os.path.join(self._cfg['%s_DOWNLOAD_PREFIX' % installKey],
                             fileName),
                fileToInstall)
            digest = self._hashUtil.calculate_hash(fileToInstall)
            self._dcm.put(fileName, fileToInstall, digest)
        # unzip
        # install to cfg determined location 'PACKAGE_INSTALL_DIR'
        #  into or CF's BUILD_DIR
        pkgKey = '%s_PACKAGE_INSTALL_DIR' % installKey
        if pkgKey in self._cfg.keys():
            installIntoDir = os.path.join(self._cfg[pkgKey],
                                          fileName.split('.')[0])
        else:
            installIntoDir = os.path.join(self._cf.BUILD_DIR,
                                          fileName.split('.')[0])
        self._unzipUtil.extract(fileToInstall, installIntoDir)
        return installIntoDir

    def install_from_build_pack(self, bpFile, toLocation=None):
        """Copy file from the build pack to the droplet

        Copies a file from the build pack to the application droplet.

            bpFile     -> file to copy, relative build pack
            toLocation -> optional location where to copy the file
                          relative to app droplet.  If not specified
                          uses the bpFile path.
        """
        fullPathFrom = os.path.join(self._cf.BP_DIR, bpFile)
        fullPathTo = os.path.join(
            self._cf.BUILD_DIR,
            ((toLocation is None) and bpFile or toLocation))
        self._safe_makedirs(os.path.dirname(fullPathTo))
        shutil.copy(fullPathFrom, fullPathTo)

    def install_from_application(self, cfgFile, toLocation):
        """Copy file from one place to another in the application

        Copies a file from one place to another place within the
        application droplet.

            cfgFile    -> file to copy, relative build pack
            toLocation -> location where to copy the file,
                          relative to app droplet.
        """
        fullPathFrom = os.path.join(self._cf.BUILD_DIR, cfgFile)
        fullPathTo = os.path.join(self._cf.BUILD_DIR, toLocation)
        self._safe_makedirs(os.path.dirname(fullPathTo))
        shutil.copy(fullPathFrom, fullPathTo)


class CloudFoundryRunner(object):
    @staticmethod
    def run_from_directory(folder, command, args, shell=False):
        if os.path.exists(folder):
            cwd = os.getcwd()
            try:
                os.chdir(folder)
                cmd = [command,]
                cmd.extend(args)
                proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell)
                stdout, stderr = proc.communicate()
                retcode = proc.poll()
                return (retcode, stdout, stderr)
            finally:
                os.chdir(cwd)

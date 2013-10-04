import os
import sys
import json
import tempfile
import shutil
from zips import UnzipUtil
from hashes import HashUtil
from cache import DirectoryCacheManager
from downloads import Downloader


class CloudFoundryUtil(object):
    def __init__(self):
        # Open stdout unbuffered
        if hasattr(sys.stdout, 'fileno'):
            sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
        # Build Pack Location
        self.BP_DIR = os.path.dirname(os.path.dirname(sys.argv[0]))
        # User's Application Files, build droplet here
        self.BUILD_DIR = sys.argv[1]
        # Cache space for the build pack
        self.CACHE_DIR = (len(sys.argv) == 3) and sys.argv[2] or None
        # Temp space
        self.TEMP_DIR = os.environ.get('TMPDIR', tempfile.gettempdir())
        # Memory Limit
        self.MEMORY_LIMIT = os.environ.get('MEMORY_LIMIT', None)
        # Make sure cache & build directories exist
        if not os.path.exists(self.BUILD_DIR):
            os.makedirs(self.BUILD_DIR)
        if self.CACHE_DIR and not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)

    def load_json_config_file_from(self, folder, cfgFile):
        return self.load_json_config_file(os.path.join(folder, cfgFile))

    def load_json_config_file(self, cfgPath):
        if os.path.exists(cfgPath):
            with open(cfgPath, 'rt') as cfgFile:
                return json.load(cfgFile)
        return {}


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
            fileToInstall = os.path.join(self._cf.TEMP_DIR, fileName)
            self._dwn.download(
                os.path.join(self._cfg['%s_DOWNLOAD_PREFIX' % installKey],
                             fileName),
                fileToInstall)
            digest = self._hashUtil.calculate_hash(fileToInstall)
            fileToInstall = self._dcm.put(fileName, fileToInstall, digest)
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

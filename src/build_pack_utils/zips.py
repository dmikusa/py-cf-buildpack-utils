import os
import gzip
import bz2
import tarfile
import zipfile
from functools import partial
from subprocess import Popen
from subprocess import PIPE


class UnzipUtil(object):

    def __init__(self, config):
        self._cfg = config

    def _unzip(self, zipFile, intoDir, stripLevel):
        zipIn = None
        try:
            zipIn = zipfile.ZipFile(zipFile, 'r')
            zipIn.extractall(intoDir)
        finally:
            if zipIn:
                zipIn.close()
        return intoDir

    def _untar(self, zipFile, intoDir, stripLevel):
        tarIn = None
        try:
            tarIn = tarfile.open(zipFile, 'r:')
            tarIn.extractall(intoDir)
        finally:
            if tarIn:
                tarIn.close()
        return intoDir

    def _gunzip(self, zipFile, intoDir, stripLevel):
        path = os.path.join(intoDir, os.path.basename(zipFile)[:-3])
        zipIn = None
        try:
            zipIn = gzip.open(zipFile, 'rb')
            with open(path, 'wb') as zipOut:
                for buf in iter(partial(zipIn.read, 8196), ''):
                    zipOut.write(buf)
        finally:
            if zipIn:
                zipIn.close()
        return path

    def _bunzip2(self, zipFile, intoDir, stripLevel):
        path = os.path.join(intoDir, os.path.basename(zipFile)[:-4])
        zipIn = None
        try:
            zipIn = bz2.BZ2File(zipFile, 'rb')
            with open(path, 'wb') as zipOut:
                for buf in iter(partial(zipIn.read, 8196), ''):
                    zipOut.write(buf)
        finally:
            if zipIn:
                zipIn.close()
        return path

    def _tar_bunzip2(self, zipFile, intoDir, stripLevel):
        return self._tar_helper(zipFile, intoDir, 'bz2', stripLevel)
    
    def _tar_gunzip(self, zipFile, intoDir, stripLevel):
        return self._tar_helper(zipFile, intoDir, 'gz', stripLevel)

    def _tar_helper(self, zipFile, intoDir, compression, stripLevel):
        # build command
        cmd = []
        if compression == 'gz':
            cmd.append('gunzip -c %s' % zipFile)
        elif compression == 'bz2':
            cmd.append('bunzip2 -c %s' % zipFile)
        else:
            raise ValueError('Invalid compression [%s]' % compression)
        if stripLevel > 0:
            cmd.append('tar xf --strip-components %d' % striplevel)
        else:
            cmd.append('tar xf -')
        # run it
        cwd = os.getcwd()
        try:
            if not os.path.exists(intoDir):
                os.makedirs(intoDir)
            os.chdir(intoDir)
            if os.path.exists(zipFile):
                proc = Popen(' | '.join(cmd), stdout=PIPE, shell=True)
                output, unused_err = proc.communicate()
                retcode = proc.poll()
                if retcode:
                    raise RuntimeError("Extracting [%s] failed with code [%d]" 
                                       % (zipFile, retcode))
        finally:
            os.chdir(cwd)
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

    def extract(self, zipFile, intoDir, stripLevel=0, method=None):
        if not method:
            method = self._pick_based_on_file_extension(zipFile)
        return method(zipFile, intoDir, stripLevel)

import os
import gzip
import bz2
import tarfile
import zipfile
from functools import partial


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

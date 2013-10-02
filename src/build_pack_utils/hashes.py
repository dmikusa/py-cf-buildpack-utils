import hashlib
from functools import partial
from subprocess import Popen
from subprocess import PIPE


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

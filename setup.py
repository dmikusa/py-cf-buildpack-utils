#!/usr/bin/env python
import os.path
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='py-cf-buildpack-utils',
      version='1.0.0',
      description='Python utilities for building CloudFoundry build packs',
      author='Daniel Mikusa',
      author_email='dan@mikusa.com',
      url='http://www.mikusa.com/projects/py-cf-buildpack-utils',
      license='Apache 2',
      keywords='cloudfoundry buildpack python',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6'
      ],
      package_dir={'': 'src'},
      py_modules=['build_pack_utils'],
      long_description=read('README'))


#!/usr/bin/env python

from distutils.core import setup

setup(name='vcon',
      version='1.0',
      description='Vcon',
      packages=['vcon'],
      install_requires=['python-jose', 'cryptography', 'hsslms', 'vcon']
     )

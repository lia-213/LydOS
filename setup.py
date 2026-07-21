#!/usr/bin/env python3

"""Package metadata and installation entry point for ugit."""

from setuptools import setup

setup(name = 'ugit',
       version = '1.0',
       packages = ['ugit'],
       entry_points = {
           'console_scripts' : [
               'ugit = ugit.cli:main'
           ]
       })
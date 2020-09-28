#!/usr/bin/env python

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

with open(os.path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='dataplate-dataaccess',
    version='0.1',
    use_scm_version=True,
    description='DataPlate Data Access API',
    long_description=README,
    author='Michael Spector',
    author_email='michael@dataplate.io',
    url='https://github.com/dataplate/dataaccess/api/python',
    license='Apache 2.0',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
    install_requires=requirements,
    packages=find_packages(),
    setup_requires=['twine', 'setuptools_scm'],
    tests_require=[],
    test_suite='tests',
)

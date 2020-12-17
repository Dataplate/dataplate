#!/usr/bin/env python

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

with open(os.path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='dataplate',
    version='0.1',
    use_scm_version=True,
    description='DataPlate API for jupyter - interact with Dataplate webserver',
    long_description=README,
    author='DataPlate team',
    author_email='info@dataplate.io',
    url='https://github.com/Dataplate/dataplate',
    license='Apache 2.0',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache 2.0",
        "Operating System :: OS Independent",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=requirements,
    packages=find_packages(),
    setup_requires=['twine', 'setuptools_scm'],
    tests_require=[],
    test_suite='tests',
    python_requires='>=3.6',
)

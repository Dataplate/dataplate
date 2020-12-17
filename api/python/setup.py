#!/usr/bin/env python

import os
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name='dataplate',
    version='0.1',
    description='DataPlate API for jupyter - interact with Dataplate webserver',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='DataPlate team',
    author_email='info@dataplate.io',
    url='https://github.com/Dataplate/dataplate',
    license='Apache 2.0',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=requirements,
    packages=find_packages(),
    python_requires='>=3.6',
)

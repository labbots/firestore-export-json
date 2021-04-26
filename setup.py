#!/usr/bin/env python

import os
import sys
from setuptools import setup

packages = []
for dirpath, dirnames, filenames in os.walk('converter'):
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)

README = None
with open(os.path.abspath('README.md')) as fh:
    README = fh.read()

with open('requirements.txt') as f:
    requirements = [x for x in f.read().splitlines() if not x.startswith("#")]

setup(
    name="fs-to-json",
    version="0.1.0",
    author='Labbots',
    author_email='labbots@users.noreply.github.com',
    license='MIT',
    packages=packages,
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    python_requires='>=3.7, <4',
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'fs_to_json=converter.command:main',
        ],
    },
)
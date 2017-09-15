#!/usr/bin/env python
from setuptools import setup
import sys


VERSION = open('version.txt').read()[:-1]


setup(
    name='pytermination',
    version=VERSION,
    description='Python Termination Analysis Module',
    long_description=open("README.md").read(),
    author='Jesus Domenech',
    author_email='jdomenec@ucm.es',
    url='https://github.com/jesusjda/pyrankfinder',
    download_url ='https://github.com/jesusjda/pyRankFinder/archive/{}.tar.gz'.format(VERSION),
    license='GPL v3',
    platforms=['any'],
    packages=['termination'],
    package_dir={'termination': 'termination'},
    package_data={'termination': ['*.py']},
    install_requires=['pplpy'],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: C++",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords=['termination', 'ranking functions', 'static analysis'],
)

#!/usr/bin/env python
from setuptools import setup
import os

base = os.path.dirname(os.path.abspath(__file__))

VERSION = open(os.path.join(base, 'version.txt')).read()[:-1]

requires = ['pplpy>=0.7', 'pyLPi', 'genericparser']

dependency_links = [
    'git+https://github.com/jesusjda/pplpy.git#egg=pplpy-0.7',
    'git+https://github.com/jesusjda/pyLPi.git#egg=pyLPi-0.1',
    'git+https://github.com/jesusjda/pyParser.git#egg=genericparser-0.1'
]

ter_dir = os.path.join(base, 'termination')
ter_name = 'termination'

inv_dir = os.path.join(base, 'invariants')
inv_name = 'invariants'

pe_dir = os.path.join(base, 'partialevaluation')
pe_name = 'partialevaluation'

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
    packages=[ter_name, inv_name],
    package_dir={ter_name: ter_dir, inv_name: inv_dir, pe_name: pe_dir},
    package_data={ter_name: ['*.py'], inv_name: ['*.py'], pe_name: ['*.py','bin/pe.sh', 'bin/*.pe']},
    install_requires=requires,
    dependency_links=dependency_links,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords=['termination', 'ranking functions', 'static analysis', 'invariants', 'partial evaluation'],
)

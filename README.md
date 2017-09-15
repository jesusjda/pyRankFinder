# pyRankFinder
Ranking Functions Finder

Documentation no up to date.
[![Documentation Status](https://readthedocs.org/projects/pyrankfinder/badge/?version=latest)](http://pyrankfinder.readthedocs.io/en/latest/?badge=latest)

<kbd>pyRankFinder</kbd> is a python module which try to find **Ranking Functions** to study termination in program's loops. 

This module has three main python-module dependencies:
- <kbd>pyLPi</kbd>
- <kbd>pyParser</kbd>
- <kbd>pplpy</kbd>

But they have a lot of other dependencies.

![](dependencies.png)

On this graph the ellipses correspond to python modules, that you
can install with pip*, and the triangles correspond to unix libraries.

\* The red ellipse indicates that you have to install the module from its corresponding repository to install the latest (unstable) version and thus support python 3.

We offer a script which install all the dependencies. <sub><sup> (Read "How to Install" section.)</sup></sub>

----------

How to Install
------------------

We recommend to have <kbd>ppl</kbd> already installed.

Then you only have to run the script: [install.sh](install.sh) <sub><sup>(it will ask you some questions.)</sup></sub>

```bash
install.sh [OPTIONS]

[OPTIONS]

    -f | --force ) 
                   force default values: Install python dependencies, 
                   but no install own modules like pyLPi.

    -l | --local ) 
                   Install local version with local modifications.
                   Otherwise, git repository version will be installed.

    -up | --update ) 
                   Update or Upgrade all the packages.

    -un | --uninstall )
                   Uninstall all except UNIX packages.

    -p=[VERSION] | --python=[VERSION] )
                   Install only for python version number [VERSION].
                   It has to be 2 or 3.
```

How to Use
---------------

There are two ways to execute this tool. 

The main file is [rankfinder.py](rankfinder.py),
you can run this command to get all the information:

```bash
$ python rankfinder.py --help
```

**(No tested yet)** The second way is: including the module [termination.py](termination/termination.py)
```python
import termination
# config must be a dictionary with all the information needed
termination.run(config)
```
**(No tested yet)** If you know what are you doing you can run inside your code a concrete algorithm, but it is no recommend if you don't know them

```python
import termination.algorithm

termination.algorithem.LexicograficRF(config)
```


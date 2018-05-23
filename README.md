# pyRankFinder
Ranking Functions Finder 

Documentation no up to date.
[![Documentation Status](https://readthedocs.org/projects/pyrankfinder/badge/?version=latest)](http://pyrankfinder.readthedocs.io/en/latest/?badge=latest)

<kbd>pyRankFinder</kbd> is a python module which try to find **Ranking Functions** to study termination in program's loops. 

This module has three main python-module dependencies:
- <kbd>pyLPi</kbd>
- <kbd>pyParser</kbd>
- <kbd>pplpy</kbd>

----------

How to Install
------------------

We recommend to have <kbd>ppl</kbd> already installed.

Then you only have to run the script: [install.sh](install.sh) <sub><sup>(it will ask you some questions.)</sup></sub>

```bash

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

Statically-Linked Binary
========================

See  [INSTRUCTIONS](./staticallylinkedbinary.md)

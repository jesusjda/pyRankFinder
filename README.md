# pyRankFinder
Ranking Functions Finder 

<!-- Documentation no up to date.
[![Documentation Status](https://readthedocs.org/projects/pyrankfinder/badge/?version=latest)](http://pyrankfinder.readthedocs.io/en/latest/?badge=latest) -->

<kbd>pyRankFinder</kbd> is a python module which try to find **Ranking
Functions** to study termination and nontermination of program's loops. 

This module has three main python-module dependencies:
- <kbd>pyLPi</kbd>
- <kbd>pyParser</kbd>
- <kbd>pplpy</kbd>

----------

## How to Install

Check the [installation info here](https://github.com/costa-group/iRankFinder/tree/master/installer#install).


## How to Use

There are two ways to execute this tool. 

The main file is [irankfinder.py](irankfinder.py),
you can run this command to get all the information:

```bash
$ python irankfinder.py --help
```

The second way is: including the module [termination](termination/)
```python
import termination
# config must be a dictionary with all the information needed
termination.analyse(algorithms, cfg)
# or for non termination
termination.analyse_nontermination(algorithms, cfg)
# where algorithms is a list of algorithm objects from termination.algorithm
```

You can also run a concrete algorithm, but it is not recomended.
```python
from termination.algorithm.lrf import PR

lrf_pr = PR()
lrf_pr.run(cfg)
```

## Statically-Linked Binary

Check [this url](https://github.com/costa-group/iRankFinder/tree/master/installer#statically-linked-binary-standalone).

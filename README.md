# pyRankFinder
Ranking Functions Finder

Documentation no up to date.
[![Documentation Status](https://readthedocs.org/projects/pyrankfinder/badge/?version=latest)](http://pyrankfinder.readthedocs.io/en/latest/?badge=latest)

<kbd>pyRankFinder</kbd> is a python module which try to find **Ranking Functions** to study termination in program's loops. 

This module has two main python modules:
- <kbd>pyLPi</kbd>
- <kbd>pyParser</kbd>

And other python dependencies:
- <kbd>argparse</kbd>

And linux dependencies:
- <kbd>ppl</kbd>
- <kbd>python-tk</kbd>
- <kbd>cython</kbd>
- <kbd>libgmp-dev</kbd>
- <kbd>libppl-dev</kbd>

----------

How to Install
------------------

We recommend to have <kbd>ppl</kbd> already installed.

Then you only have to run the script: [install.sh](install.sh)

If there are changes on some of the three repositories (pyRankFinder, pyLPi, pyParser),
you can update them by running: [update.sh](update.sh)

How to Use
---------------

There are two ways to execute this tool. 

The main file is [RankFinder.py](pyRankFinder/RankFinder.py),
you can run this command to get all the information:
> RankFinder.py --help


**(No tested yet)** The second way is: including the module [Termination.py](pyRankFinder/Termination.py)
> import Termination
>
> \# config must be a dictionary with all the information needed
> 
> Termination.run(config)

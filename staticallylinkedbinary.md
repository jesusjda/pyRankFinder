Statically linked binary
========================

It is needed: `pyinstaller`.
`$ pip install pyinstaller`

You will also need the tool installed:
    - `pip install git+https://github.com/jesusjda/pplpy`
    - `pip install git+https://github.com/jesusjda/pyLPi#egg=lpi`
    - `pip install git+https://github.com/jesusjda/pyParser#egg=genericparser`
    - `pip install git+https://github.com/jesusjda/pyRankFinder#egg=termination`

Generate Binary
===============

Path to sources (maybe it is not needed)
```
PPATH=/home/friker/Systems/pplpy/ppl/:/home/friker/Systems/pyLPi/lpi/:/home/friker/Systems/pyParser/genericparser/:/home/friker/Systems/pyRankFinder/partialevaluation/:/home/friker/Systems/pyRankFinder/invariants/:/home/friker/Systems/pyRankFinder/termination/
```


```
pyinstaller rankfinder.py --hidden-import networkx --hidden-import gmpy2 --hidden-import cython --hidden-import cysignals --hidden-import z3 --hidden-import eiol --hidden-import lark --hidden-import pkg_resources.extern.packaging.version --hidden-import genericparser --hidden-import genericparser.Parser_smt2 --hidden-import genericparser.Parser_fc --hidden-import genericparser.Parser_koat --hidden-import termination --hidden-import invariants --hidden-import lpi --hidden-import ppl   -p $PPATH
```

Copy no python files:
     - all grammar files of genericparser
     - smt2pushdown binary
```
mkdir ./dist/rankfinder/genericparser/
cp ../pyParser/genericparser/*.g ./dist/rankfinder/genericparser/
cp ../pyParser/genericparser/smtpushdown2 ./dist/rankfinder/genericparser/smtpushdown2
mkdir -p ./dist/rankfinder/lark/grammars/
cp /usr/local/lib/python3.5/dist-packages/lark/grammars/common.g /home/friker/Systems/pyRankFinder/dist/rankfinder/lark/grammars/common.g
```

Test
====

Test with:
```
./dist/rankfinder/rankfinder -f ./test/Ackermann.jar-obl-8.smt2 -t qnlrf_1 -sccd 1
```
The answer should be equivalent to:
```
Final Termination Result
FOUND:
f138_0_ack_GT: < < arg2 >, < arg2 >, < arg1 > >
```

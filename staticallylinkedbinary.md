stalStatically linked binary
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
BBASE=
PPATH=$BBASE/pplpy/ppl/:$BBASE/pyLPi/lpi/:$BBASE/pyParser/genericparser/:$BBASE/pyRankFinder/partialevaluation/:$BBASE/pyRankFinder/nodeproperties/:$BBASE/pyRankFinder/termination/
```


```
pyinstaller irankfinder.py --hidden-import networkx --hidden-import gmpy2 --hidden-import cython --hidden-import cysignals --hidden-import z3 --hidden-import eiol --hidden-import lark --hidden-import pkg_resources.extern.packaging.version --hidden-import genericparser --hidden-import genericparser.Parser_smt2 --hidden-import genericparser.Parser_fc --hidden-import genericparser.Parser_koat --hidden-import termination --hidden-import nodeproperties --hidden-import lpi --hidden-import ppl -p $PPATH
```

Copy no python files:

     - all grammar files of genericparser
     - smt2pushdown binary
     - PE binary

```
mkdir ./dist/irankfinder/genericparser/
cp ../pyParser/genericparser/*.g ./dist/irankfinder/genericparser/
cp ../pyParser/genericparser/smtpushdown2 ./dist/irankfinder/genericparser/smtpushdown2
mkdir -p ./dist/irankfinder/lark/grammars/
cp /usr/local/lib/python3.5/dist-packages/lark/grammars/common.g ./dist/irankfinder/lark/grammars/common.g
mkdir -p ./dist/irankfinder/partialevaluation/bin/
cp partialevaluation/bin/* ./dist/irankfinder/partialevaluation/bin/

```

Test
====

Test with:
```
./dist/irankfinder/irankfinder -f ./test/Ackermann.jar-obl-8.smt2 -t qnlrf_1 -sccd 1
```
The answer should be something similar to:
```
Final Termination Result
FOUND:
f138_0_ack_GT: < < arg2 >, < arg2 >, < arg1 > >
```

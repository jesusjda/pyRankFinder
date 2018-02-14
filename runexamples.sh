#!/bin/bash

source=$1
chars=${@:2}
cache="/home/friker/tmp/cache"
for x in $chars; do
    examples="/home/friker/Projects/jesusjda/easyinterface-config/examples/smt2/From_"$source"/"$x"/*.smt2"
    PYRF="/home/friker/Systems/pyRankFinder/runexamples.py"
    python3 $PYRF -v 0 -to 180 -sccd 5 -c $cache -f $examples
done

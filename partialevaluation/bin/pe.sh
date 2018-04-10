#!/bin/sh
# $1 - file
# $2 - props level [ "full", "simple" ]
# $3 - propsfilename

BASEDIR=$(dirname "$0")

$BASEDIR/props_$2.pe -prg $1 -o $3 &&
$BASEDIR/peunf.pe -prg $1 -entry "startpoint" -props $3

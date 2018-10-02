#!/bin/bash

# $1 - file
# $2 - initial goal

# -d flag if present for drawing cfg
# -p flag if present for print cfg in fc format
# -l N option to select the level of props (default. 4)
# -r PATH option to select destination folder (default. $1_output/)

PEPATH=$(dirname $0)
export LD_LIBRARY_PATH=$PATH":"$PEPATH

OPTS=`getopt -o r:l: --long result-dir:,draw -n "$0" -- "$@"`
if [ $? != 0 ] ; then echo "Failed parsing options." >&2; exit 1; fi

eval set -- "$OPTS"

draw=false
level=4
print=false
while true; do
   case "$1" in
       -l) level=$2; shift 2;
	   ;;
       -r|--result-dir) resultdir=$2; shift 2;
	   ;;
       -- ) shift; break ;;
       * ) break ;;
   esac
done

if [ $# -gt 1 ]; then echo "Too many arguments." >&2; exit 1; fi
if [ $# -eq 0 ]; then echo "Missing file." >&2; exit 1; fi
if [ ! -f "$1" ]; then echo 'File "'$1'" not found.' >&2; exit 1; fi
if [[ -z ${resultdir+x} ]]; then resultdir=$(dirname $1); fi



f=`basename $1`
f=${f%.pl} # remove .pl extension
resultdir=$resultdir/${f}_output

if [ ! -d $resultdir ]; then
    mkdir -p $resultdir
    if [ $? != 0 ]; then echo "Error when creating $resultdir folder" >&2; exit 1; fi
fi

if [ "$level" == "0" ]; then
	touch "$resultdir/$f.props"
else
	$PEPATH/props -prg "$1" -l "$level" -o "$resultdir/$f.props"
	if [ $? != 0 ]; then echo "Error: error computing the properties." >&2; exit 1; fi
fi
echo -n "$resultdir/$f.props"
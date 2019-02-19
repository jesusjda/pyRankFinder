#!/bin/bash -e

# $1 - file
# $2 - initial goal

# -r destination file

PEPATH=$(dirname $0)
export LD_LIBRARY_PATH=$PATH":"$PEPATH

OPTS=`getopt -o r:l: --long result-file: -n "$0" -- "$@"`
if [ $? != 0 ] ; then echo "Failed parsing options." >&2; exit 1; fi

eval set -- "$OPTS"


print=false
while true; do
   case "$1" in
       -r|--result-file) resultfile=$2; shift 2;
	   ;;
       -- ) shift; break ;;
       * ) break ;;
   esac
done

if [ $# -gt 2 ]; then echo "Too many arguments." >&2; exit 1; fi
if [ $# -lt 2 ]; then echo "Missing file or initial goal" >&2; exit 1; fi
if [ ! -f "$1" ]; then echo 'File "'$1'" not found.' >&2; exit 1; fi
if [[ -z ${resultfile+x} ]]; then resultfile=$(dirname $1)"/"$(basename $1)".props"; fi

echo "$2"
$PEPATH/props1 -prg "$1" -entry "$2" -o "$resultfile"


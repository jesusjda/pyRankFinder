#!/bin/bash

basedir=$(dirname "$(readlink -f "$0" )")
pvers="false"
P3=false
P2=false
LOCAL=false
UP=false
UnixPKG=true
for i in "$@"; do
    case $i in
	-p=*|--python=*)
	    pvers="${i#*=}"
	    if [ "$pvers" = "2" ]; then
		P2=true
	    fi
	    if [ "$pvers" = "3" ]; then
		P3=true
	    fi
	    shift 
	    ;;
	-nu|--no-unix-packages)
	    UnixPKG=false
	    shift
	    ;;
	-l|--local)
	    LOCAL=true
	    shift
	    ;;
	-up|--update)
	    UP=true
	    shift
	    ;;
	*)
	    >&2 cat  <<EOF 
ERROR: $0 [OPTIONS]

[OPTIONS]

    -p=[VERSION] | --python=[VERSION] )
        Install only for python version number [VERSION].
        It has to be 2 or 3.

    -nu | --no-unix-packages)
        Prevent to install unix packages like python-dev or libppl-dev.
        Use this parameter if you have already satisfied the dependencies.

    -l | --local ) 
        Install local version with local modifications.
        Otherwise, git repository version will be installed.

    -up | --update ) 
        Update or Upgrade all the packages.


EOF
	    exit -1
            # unknown option
	    ;;
    esac
done

if [ "$P3" == "false" -a "$P2" == "false" ]; then
    echo "ERROR at least one python use: -p=[VERSION]" >&2
    exit -1
fi

parampython=""
if [ "$P2" == "true" ]; then
    parampython=$parampython" -p=2"
fi
if [ "$P3" == "true" ]; then
    parampython=$parampython" -p=3"
fi

if [ "$UP" == "false" ]; then
    param=$parampython
    if [ "$UnixPKG" == "false" ]; then
	param=$param" -nu"
    fi
    $basedir/install_dependencies.sh $param
fi

param=$parampython
if [ "$LOCAL" == "true" ]; then
    param=$param" -l"
fi

$basedir/install_module.sh $param

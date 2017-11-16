#!/bin/bash

pvers="false"
P3=false
P2=false
LOCAL=false
UP=false
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
	-l|--local)
	    LOCAL=true
	    shift
	    ;;
	*)
	    >&2 cat  <<EOF 
ERROR: $0 [OPTIONS]

[OPTIONS]

    -p=[VERSION] | --python=[VERSION] )
        Install only for python version number [VERSION].
        It has to be 2 or 3.

    -l | --local ) 
        Install local version with local modifications.
        Otherwise, git repository version will be installed.


EOF
	    exit -1
            # unknown option
	    ;;
    esac
done

install_module(){
    flags="--upgrade"
    vers=$1
    mkdir -p /tmp/pyeiol
    pushd /tmp/pyeiol
    git clone https://github.com/abstools/easyinterface.git .
    git checkout develop
    cd ./outputlanguage/python
    python$vers -m pip install $flags .
    popd
    # python$vers -m pip install $flags "git+https://github.com/abstools/easyinterface.git@develop#egg=pyeiol&subdirectory=outputlanguage/python"
    # python$vers -m pip install $flags "git+https://github.com/jesusjda/pyLPi.git#egg=pyLPi" --process-dependency-links
    # python$vers -m pip install $flags "git+https://github.com/jesusjda/pyParser.git#egg=genericparser" --process-dependency-links
    if [ "$LOCAL" == "true" ]; then
	python$vers -m pip install $flags . --process-dependency-links
    else
	python$vers -m pip install $flags --process-dependency-links "git+https://github.com/jesusjda/pyRankFinder.git#egg=pytermination"
    fi
}

if [ "$P3" == "false" -a "$P2" == "false" ]; then
    echo "ERROR at least one python use: -p=[VERSION]" >&2
    exit -1
fi

if [ "$P2" == "true" ]; then
    install_module 2
fi

if [ "$P3" == "true" ]; then
    install_module 3
fi

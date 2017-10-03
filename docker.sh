#!/bin/bash


exists(){
    command -v "$1" >/dev/null 2>&1
}

install_apt(){
    if exists $1; then
	echo $1
	true
    else
	apt-get install -y $1
    fi
}

install_all(){
    for app in $@; do
	install_apt $app
    done
}

install_module(){
    vers=$1
    python$vers -m pip install z3 'Cython==0.26' virtualenv
    python$vers -m pip install cysignals 
    python$vers -m pip install git+https://github.com/aleaxit/gmpy.git@gmpy2-2.1.0a0#egg=gmpy2
    python$vers -m pip install git+https://github.com/videlec/pplpy.git#egg=pplpy
    python$vers -m pip install git+https://github.com/jesusjda/pyLPi.git#egg=pyLPi
    python$vers -m pip install pydot pydotplus
    python$vers -m pip install networkx
    python$vers -m pip install arpeggio
    python$vers -m pip install git+https://github.com/jesusjda/pyParser.git#egg=pyParser
    python$vers -m pip install git+https://github.com/jesusjda/pyRankFinder.git#egg=pytermination
}


basedir=$(dirname "$(readlink -f "$0" )")
FORCE=false
pvers="false"
P3=false
P2=false
LOCAL=false
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
	-f|--force)
	    FORCE=true
	    shift 
	    ;;
	-l|--local)
	    LOCAL=true
	    shift
	    ;;
	*)
	    >&2 cat  <<EOF 
ERROR: docker.sh [OPTIONS]

[OPTIONS]

    -f | --force ) 
                   force default values: Install python dependencies, 
                   but no install own modules like pyLPi.

    -l | --local ) 
                   Install local version with local modifications.
                   Otherwise, git repository version will be installed.

    -p=[VERSION] | --python=[VERSION] )
                   Install only for python version number [VERSION].
                   It has to be 2 or 3.

EOF
	    exit -1
            # unknown option
	    ;;
    esac
done

# INSTALL ppl
install_all libgmp-dev libmpfr-dev libmpc-dev
if exists ppl-config; then
    mkdir /tmp/ppl
    cd /tmp/ppl
    wget http://bugseng.com/products/ppl/download/ftp/releases/1.2/ppl-1.2.tar.gz
    gunzip ppl-1.2.tar.gz
    tar xvfp ppl-1.2.tar
    cd ppl-1.2
    ./configure --prefix=/usr/local --with-gmp=/opt/local --enable-interfaces="swi_prolog,c++"
    make
    make install
    # chmod a+rwx -R /usr/local/lib/ppl
fi

apt-get -y update
install_all libppl-dev graphviz
if [ "$P2" == "true" ]; then
    install_all -y python python-dev python-nose python-pip
    install_module 2
fi

if [ "$P3" == "true" ]; then
    install_all -y python3 python3-dev python3-nose python3-pip
    install_module 3
fi


#!/bin/bash

P3=false
P2=false
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

EOF
	    exit -1
            # unknown option
	    ;;
    esac
done

if [ "$P3" == "false" -a "$P2" == "false" ]; then
    echo "ERROR at least one python use: --python=[VERSION]" >&2
    exit -1
fi

exists(){
    command -v "$1" >/dev/null 2>&1
}

install_apt(){
    apt-get install -y $@
}

install_all(){
    if [ "$UnixPKG" == "true" ]; then
	install_apt $@
    fi
}

install_dependencies(){
    vers=$1
    python$vers -m pip install z3-solver 'Cython==0.26' virtualenv
    python$vers -m pip install cysignals
    python$vers -m pip install "git+https://github.com/aleaxit/gmpy.git@gmpy2-2.1.0a0#egg=gmpy2"
}

if [ "$UnixPKG" == "true" ]; then
    apt-get -y update
    # INSTALL ppl
    install_all libgmp-dev libmpfr-dev libmpc-dev

    if exists ppl-config; then
	echo "PPL already installed"
    else
	mkdir /tmp/ppl
	pushd /tmp/ppl
	wget http://bugseng.com/products/ppl/download/ftp/releases/1.2/ppl-1.2.tar.gz
	gunzip ppl-1.2.tar.gz
	tar xvfp ppl-1.2.tar
	cd ppl-1.2
	./configure --prefix=/usr/local --with-gmp=/opt/local --enable-interfaces="swi_prolog,c++"
	make
	make install
	popd
	# chmod a+rwx -R /usr/local/lib/ppl
    fi
    install_all libppl-dev graphviz

fi

if [ "$P2" == "true" ]; then
    install_all -y python python-dev python-nose python-pip
    install_dependencies 2
fi

if [ "$P3" == "true" ]; then
    install_all -y python3 python3-dev python3-nose python3-pip
    install_dependencies 3
fi

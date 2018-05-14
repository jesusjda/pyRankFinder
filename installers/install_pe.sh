#!/bin/bash

install_ciao(){
    dpkg-query -W ciaode 2> /dev/null
    if [[ "$?" == "0" ]]; then
	echo "Ciao already installed."
	exit 0;
    fi

    mkdir -p /tmp/ciao
    git clone https://github.com/ciao-lang/ciao.git /tmp/ciao
    pushd /tmp/ciao
    SHELL_BACKUP=$SHELL
    export SHELL=/bin/sh # (otherwise build fails)
    ./ciao-boot.sh local-install --with-docs=no
    export SHELL=$SHELL_BACKUP
    popd
}

install_ciao_libs(){
    ciao get ciao_ppl
    ciao get github.com/jfmc/ciao_yices
    ciao get github.com/bishoksan/chclibs
    ciao get github.com/bushokdsan/RAHFT
}

install_pe(){
    install_ciao_libs
    mkdir -p $PEPATH
    git clone  https://github.com/jpgallagher/pe.git $PEPATH
    pushd $PEPATH
    ciaoc chc2cfg
    ciaoc drawcfg
    #pecfg.sh 
    ciaoc peunf
    ciaoc peunf_smt
    ciaoc peunf_smt_2
    popd
    
}

PEPATH=${PEPATH:-"/opt/pe"}

install_ciao
install_pe


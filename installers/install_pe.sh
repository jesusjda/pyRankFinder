#!/bin/bash

install_ciao(){
    dpkg-query -W ciaode 2> /dev/null
    if [[ "$?" == "0" ]]; then
	echo "Ciao already installed."
	exit 0;
    fi

    mkdir -p /tmp/ciao
    git clone https://github.com/ciao-lang/ciao.git /tmp/ciao
    /tmp/ciao/ciao-boot.sh local-install
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
PETOOL=$PEPATH/pecfg.sh

install_ciao
install_pe

echo "consider to add PETOOL=$PETOOL to the environment"

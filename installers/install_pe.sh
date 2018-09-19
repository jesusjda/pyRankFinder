#!/bin/bash

set -e

install_ciao(){
    dpkg-query -W ciaode 2> /dev/null && { echo "Ciao already installed."; exit 0; }

    mkdir -p $CIAO_HOME
    echo "[1/2] Cloning Ciao git"
    git clone https://github.com/ciao-lang/ciao.git $CIAO_HOME
    echo "[2/2] Installing ciao core"
    pushd $CIAO_HOME
    SHELL_BACKUP=$SHELL
    export SHELL=/bin/sh # (otherwise build fails)
    ./ciao-boot.sh local-install --with-docs=no --prefix=${CIAO_HOME/\/ciao/} > /dev/null
#    export SHELL=$SHELL_BACKUP
    popd
    echo "end ciao"
}

install_ciao_libs(){
    # ciao_ppl
    # No Requirements
    echo "libs [1/5] installing ciao_ppl"
    ciao get ciao_ppl > /dev/null
    # ciao_yices
    echo "libs [2/5] installing yices dependencies"
    apt-get -y install gperf  > /dev/null
    echo "libs [3/5] installing ciao_yices"
    ciao get github.com/jfmc/ciao_yices > /dev/null
    # chclibs
    # No Requirements
    echo "libs [4/5] installing chclibs"
    ciao get github.com/bishoksan/chclibs > /dev/null
    # RAHFT
    # No Requirements
    echo "libs [5/5] installing RAHFT"
    ciao get github.com/bishoksan/RAHFT > /dev/null
    echo "end libs."
}

install_pe(){
    install_ciao_libs
    mkdir -p $PEPATH
    git clone  https://github.com/jpgallagher/pe.git $PEPATH
    pushd $PEPATH
    ciaoc chc2cfg
    ciaoc drawcfg
    ciaoc peunf
    ciaoc peunf_smt
    ciaoc peunf_smt_2
    # pecfg.sh 
    popd
    
}

PEPATH=${PEPATH:-"/opt/pe"}
CIAO_HOME=${CIAO_HOME:-"/opt/ciao"}


install_ciao
if [ -x $CIAO_HOME/build/bin/ciao-env ] ; then
    eval "$($CIAO_HOME/build/bin/ciao-env --sh)"
fi

install_pe


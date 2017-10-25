#!/bin/bash


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
    python$vers -m pip install "git+https://github.com/videlec/pplpy.git#egg=pplpy"
    python$vers -m pip install pydot pydotplus
    python$vers -m pip install networkx
    python$vers -m pip install arpeggio
}

install_module(){
    flags=""
    if [ "$UP" == "true" ]; then
        flags=" --upgrade "
    fi
    vers=$1
    python$vers -m pip install $flags "git+https://github.com/abstools/easyinterface.git@develop#egg=pyeiol&subdirectory=outputlanguage/python"
    python$vers -m pip install $flags "git+https://github.com/jesusjda/pyLPi.git#egg=pyLPi"
    python$vers -m pip install $flags "git+https://github.com/jesusjda/pyParser.git#egg=pyParser"
    python$vers -m pip install $flags "git+https://github.com/jesusjda/pyRankFinder.git#egg=pytermination"
}

install_t2(){
    install_all mono-complete mono-xbuild fsharp
    Z3DIR=/opt/tools/z3
    T2DIR=/opt/tools/t2
    NUGET=/opt/tools/nuget.exe

    # Build Z3
    mkdir -p $Z3DIR
    mkdir -p $T2DIR
    pushd $Z3DIR
    git clone https://bitbucket.org/spacer/code
    cd code
    git checkout spacer-t2
    ./configure
    cd build
    make
    popd
    
    # Install nuget
    curl https://dist.nuget.org/win-x86-commandline/latest/nuget.exe > $NUGET

    # Build .NET bindings for z3
    pushd $Z3DIR"/code/src/api/dotnet/"
    xbuild Microsoft.Z3.csproj
    popd

    # Update z3 and its .NET bindings in the T2 source tree:
    cp "$Z3DIR/src/api/dotnet/obj/Debug/Microsoft.Z3.*" "$T2DIR/src/"
    cp "$Z3DIR/build/libz3.*" "$T2DIR/src/"

    # Get required packages via NuGet (may need to import certificates first):
    mozroots --import --sync
    pushd "$T2DIR/src"
    mono nuget restore
    chmod +x packages/FsLexYacc.*/build/*exe
    popd

    # Build T2, Release configuration:
    pushd "$T2DIR/src" && xbuild /property:Configuration=Release && popd

    pushd "$T2DIR/test" && mono "$T2DIR/src/bin/Release/T2.exe" -tests
}


basedir=$(dirname "$(readlink -f "$0" )")
pvers="false"
P3=false
P2=false
LOCAL=false
T2=false
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
	-t2|--t2)
	    T2=true
	    shift
	    ;;
	-up|--update)
	    UP=true
	    shift 
	    ;;
	*)
	    >&2 cat  <<EOF 
ERROR: docker.sh [OPTIONS]

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

if [ "$UnixPKG" == "true" ]; then
    apt-get -y update
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
    install_all libppl-dev graphviz

fi



if [ "$P2" == "true" ]; then
    install_all -y python python-dev python-nose python-pip
    if [ "$UP" == "false" ]; then
	install_dependencies 2
    fi
    install_module 2
fi

if [ "$P3" == "true" ]; then
    install_all -y python3 python3-dev python3-nose python3-pip
    install_dependencies 3
    install_module 3
fi

if [ "$T2" == "true" ]; then
    install_t2
fi

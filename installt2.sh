#!/bin/bash
UnixPKG=true
install_apt(){
    apt-get install -y $@

}

install_all(){
    if [ "$UnixPKG" == "true" ]; then
	install_apt $@
    fi
}

install_t2(){
    # Add mono sources 
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
    echo "deb http://download.mono-project.com/repo/ubuntu xenial main" | sudo tee /etc/apt/sources.list.d/mono-official.list
    
    # Install dependencies
    apt-get update
    install_all build-essential python mono-devel fsharp ca-certificates-mono 

    Z3DIR=/opt/tools/z3
    T2DIR=/opt/tools/t2
    NUGET=/opt/tools/nuget.exe

    # Install nuget
    curl https://dist.nuget.org/win-x86-commandline/v4.1.0/nuget.exe > $NUGET

    git clone https://github.com/mmjb/T2.git $T2DIR

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

    # Build .NET bindings for z3
    pushd $Z3DIR"/code/"
    python scripts/mk_make.py
    cd build
    make
    make install
    
    # xbuild Microsoft.Z3.csproj
    popd



    # Update z3 and its .NET bindings in the T2 source tree:
    cp $Z3DIR/code/src/api/dotnet/obj/Debug/Microsoft.Z3.* $T2DIR/src/
    cp $Z3DIR/code/build/libz3.* $T2DIR/src/
    

    # Get required packages via NuGet (may need to import certificates first):
    cert-sync /etc/ssl/certs/ca-certificates.crt
    pushd "$T2DIR/src"
    mono $NUGET restore
    chmod +x packages/FsLexYacc.*/build/*exe
    popd
    
    # Build T2, Release configuration:
    pushd "$T2DIR/src" && xbuild /property:Configuration=Release && popd

     #pushd "$T2DIR/test" && mono "$T2DIR/src/bin/Release/T2.exe" -tests
}

install_t2

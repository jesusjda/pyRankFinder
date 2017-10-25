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
    install_all build-essential python mono-complete mono-xbuild fsharp
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
    mono $NUGET restore
    chmod +x packages/FsLexYacc.*/build/*exe
    popd

    # Build T2, Release configuration:
    pushd "$T2DIR/src" && xbuild /property:Configuration=Release && popd

    pushd "$T2DIR/test" && mono "$T2DIR/src/bin/Release/T2.exe" -tests
}

install_t2

#!/bin/bash

getGitDependencies(){
    BASEDIR=$1
    NAME=$2
    GITURL=$3
    echo "Checking git $NAME"
    if [ ! -d $BASEDIR/$NAME ]; then
	if [ -d $BASEDIR/../$NAME ]; then
	    ln -s $BASEDIR/../$NAME $BASEDIR/$NAME
	else
	    git clone $GITURL $BASEDIR/$NAME
	fi
    else
	cd $BASEDIR/$NAME
	git pull
	cd $BASEDIR
    fi
}

checkAndInstall(){
    for PKG in "$@"
    do
	PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $PKG|grep "install ok installed")
	echo Checking for $PKG: $PKG_OK
	if [ "" == "$PKG_OK" ]; then
	    echo "No $PKG. Setting up $PKG."
	    sudo apt-get --force-yes --yes install $PKG
	fi
    done
}

installDependencies(){
    BASEDIR=$1
    NAME=$2
    if [ -f $BASEDIR/$NAME/requirements.apt ]; then
	checkAndInstall $(<$BASEDIR/$NAME/requirements.apt)
    fi

    if [ -f $BASEDIR/$NAME/requirements.pip ]; then
	sudo -H pip2.7 install -r $BASEDIR/$NAME/requirements.pip
    fi
}

# echo "pwd: `pwd`"
# echo "\$0: $0"
# echo "basename: `basename $0`"
# echo "dirname: `dirname $0`"
# echo "dirname/readlink: $(dirname $(readlink -f $0))"
BASEDIR=$(dirname $(readlink -f $0))
getGitDependencies $BASEDIR "pyLPi" "https://github.com/jesusjda/pyLPi"
getGitDependencies $BASEDIR "pyParser" "https://github.com/jesusjda/pyParser"

installDependencies $BASEDIR "pyLPi"
installDependencies $BASEDIR "pyParser"

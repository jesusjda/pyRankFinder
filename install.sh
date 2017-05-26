#!/bin/bash

getGitDependencies(){
    echo "Checking git $2"
    if [ ! -d $1/$2 ]; then
	if [ -d $1/../$2 ]; then
	    ln -s $1/../$2 $1/$2
	else
	    git clone $3 $1/$2
	fi
    else
	cd $1/$2
	git pull
	cd $1
    fi
    installDependencies $1/$2
}

checkAndInstall(){
    PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $PKG|grep "install ok installed")
    echo Checking for $PKG: $PKG_OK
    if [ "" == "$PKG_OK" ]; then
	echo "No $PKG. Setting up $PKG."
	sudo apt-get --force-yes --yes install $PKG
    fi
}

installDependencies(){
    if [ -f $1/requirements.apt ]; then
	for PKG in $(<$1/requirements.apt) ; do
	    checkAndInstall $PKG
	done
    fi

    if [ -f $1/requirements.pip ]; then
	sudo -H pip2.7 install -r $1/requirements.pip
    fi

    if [ -f $1/requirements.git ]; then
	while read GIT; do
	    getGitDependencies $1 $GIT
	done <$1/requirements.git
    fi
}

installDependencies $(dirname $(readlink -f $0))


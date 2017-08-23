#!/bin/bash

getGitDependencies(){
    echo "Checking git $2"
    if [ ! -d $1/lib/$2 ]; then
	if [ -d $1/../$2 ]; then
	    ln -s $1/../$2 $1/lib/$2
	else
	    git clone $3 $1/lib/$2
	fi
    else
	cd $1/lib/$2
	git pull
	python setup.py sdist
	sudo python setup.py install
	cd $1
    fi
    installDependencies $1/lib/$2
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
    if [ "$(uname -s)" = 'Linux' ]; then
	if [ -f $1/requirements.apt ]; then
	    for PKG in $(<$1/requirements.apt) ; do
		checkAndInstall $PKG
	    done
	fi
    else
	echo "Assuming you have pre-installed"
	cat $1/requeriments.apt
    fi

    if [ -f $1/requirements.pip ]; then
	# sudo -H pip2 install -r $1/requirements.pip
	sudo -H pip install -r $1/requirements.pip
    fi

    if [ -f $1/requirements.git ]; then
	while read GIT; do
	    getGitDependencies $1 $GIT
	done <$1/requirements.git
    fi
}

if [ "$(uname -s)" = 'Linux' ]; then
    basedir=$(dirname "$(readlink -f "$0" )")
else
    basedir=$(dirname "$(readlink "$0" )")
fi

# installDependencies $basedir





while true; do
    read -p "Do you wish to install own modules (pyParser, pyLPi)? [Y/n] " yn
    case $yn in
        [YySs]* | "") echo "Installing..."; installModules
        [Nn]* ) echo "no";;
        * ) echo "Invalid option."; echo $yn;;
    esac
done

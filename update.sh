#!/bin/bash

getGitDependencies(){
    echo "Checking git $2"
	cd $1/lib/$2
	git pull
	cd $1
}

installDependencies(){
    if [ -f $1/requirements.git ]; then
	while read GIT; do
	    getGitDependencies $1 $GIT
	done <$1/requirements.git
    fi
}
echo "Checking git pyRankFinder"
git pull
installDependencies $(dirname $(readlink -f $0))

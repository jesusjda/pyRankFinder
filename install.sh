#!/bin/bash

UN=""
UP=""
FORCE=false
pvers="false"
P3=false
P2=false
LOCAL=false
for i in "$@"; do
    case $i in
	-up|--update)
	    UP="up"
	    UN=""
	    shift 
	    ;;
	-un|--uninstall)
	    UP=""
	    UN="un"
	    shift 
	    ;;
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
	-f|--force)
	    FORCE=true
	    shift 
	    ;;
	-l|--local)
	    LOCAL=true
	    shift
	    ;;
	*)
	    >&2 cat  <<EOF 
ERROR: install.sh [OPTIONS]

[OPTIONS]

    -f | --force ) 
                   force default values: Install python dependencies, 
                   but no install own modules like pyLPi.

    -l | --local ) 
                   Install local version with local modifications.
                   Otherwise, git repository version will be installed.

    -up | --update ) 
                   Update or Upgrade all the packages.

    -un | --uninstall )
                   Uninstall all except UNIX packages.

    -p=[VERSION] | --python=[VERSION] )
                   Install only for python version number [VERSION].
                   It has to be 2 or 3.

EOF
	    exit -1
            # unknown option
	    ;;
    esac
done


exists(){
    command -v "$1" >/dev/null 2>&1
}


if [ "$pvers" = "false" ]; then
    if exists python2; then
	P2=true
    else
	P2=false
    fi
    
    if exists python3; then
	P3=true
    else
	P3=false
    fi
fi

flags=""

# check sudo permission
if [ "$EUID" -ne 0 ]; then
    flags=$flags" --user"
fi


# get base folder
if [ "$(uname -s)" = 'Linux' ]; then
    basedir=$(dirname "$(readlink -f "$0" )")
else
    basedir=$(dirname "$(readlink "$0" )")
fi

# Python 2 or 3 or both?
while [ "$P2" = "true" -a "$P3" = "true" ]; do
    read -p "Which python version do you want to use? [2/3/B] (default: B - Both) " yn
    case $yn in
        [2]*)
	    P3=false
	    break;;
	[3]* )
	    P2=false
	    break;;
        ""|[bB])
	    break;;
        * ) echo "Invalid option."; echo $yn;;
    esac
done


if [ "$FORCE" = "true" ]; then
    mdepen=true
else

    mdepen=true
    while true; do
	read -p "Do you want to "$UN"install the dependencies? [Y/n]" yn
	case $yn in
            [yY][eE][sS]|[yY])
		break;;
	    [nN][oO]|[nN])
		mdepen=false
		break;;
            "")
		break;;
            * ) echo "Invalid option."; echo $yn;;
	esac
    done

fi


install()
{
    lflags=$flags
    if [ "$UN" = "un" ]; then
	lflags=" -y"
    elif [ "$UP" = "up" ]; then	
	lflags=$lflags" --upgrade"
    fi
    lvers=$1
    if [ "$mdepen" = "true" ]; then
	fl=""
	if [ "$UN" = "un" ]; then
	    fl="--uninstall"
	elif [ "$UP" = "up" ]; then
	    fl="--update"
	fi
	cwd=$(pwd)
	mkdir $basedir/tmplpi
	git clone https://github.com/jesusjda/pyLPi.git $basedir/tmplpi/
	cd $basedir/tmplpi
	$basedir/tmplpi/install.sh -f $fl -p=$lvers
	cd $cwd
	rm -rf $basedir/tmplpi
	mkdir $basedir/tmpparser
	git clone https://github.com/jesusjda/pyParser.git $basedir/tmpparser/
	cd $basedir/tmpparser
	$basedir/tmpparser/install.sh -f $fl -p=$lvers
	cd $cwd
	rm -rf $basedir/tmpparser
    fi

    echo "----------------------------------------"
    echo "Installing pyRankFinder on Python $lvers"
    echo "----------------------------------------"

    if [ "$LOCAL" = "true" ]; then
	pip$lvers $UN"install" $lflags .
    else
	pip$lvers $UN"install" $lflags git+https://github.com/jesusjda/pyRankFinder.git#egg=pyRankFinder
    fi
} 

if [ "$P2" = "true" ]; then
    easy_install $flags pip
    install 2
fi

if [ "$P3" = "true" ]; then
    easy_install3 $flags pip
    install 3
fi


echo "Success!"

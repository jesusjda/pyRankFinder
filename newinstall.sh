#!/bin/bash

# Python 2 or 3 or both?
P2=true
P3=true
while true; do
    read -p "Which python version do you want to use? [2/3/B] (default: B - Both)" yn
    case $yn in
        [2]*)
	    echo "Python 2...";
	    P3=false
	    break;;
	[3]* )
	    echo "Python 3...";
	    P2=false
	    break;;
        "")
	    echo "Python 2 and 3";
	    break;;
        * ) echo "Invalid option."; echo $yn;;
    esac
done

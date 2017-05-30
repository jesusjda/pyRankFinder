import os
import sys
import getopt
import GeneralParser as Parser
from LP import *

def Main(argv):
    try:
        opts, args = getopt.getopt(argv,"",[])
    except getopt.GetoptError:
        print(help())
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help())
        elif opt in ("-a", "--algorithm"):
            print("To be done..")
    print("BYE")

if __name__ == "__main__":
    # Main(sys.argv[1:])
    x = Variable(0)
    x._dont

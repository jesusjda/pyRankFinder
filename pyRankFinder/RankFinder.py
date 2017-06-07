import os
import sys
import getopt

def test():
    return 

def Main(argv):
    try:
        opts, args = getopt.getopt(argv,"",[])
    except getopt.GetoptError:
        print(help())
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help())
            sys.exit(0)
        elif opt in ("-a", "--algorithm"):
            print("To be done..")
    print("BYE")

if __name__ == "__main__":
    # Main(sys.argv[1:])
    a, b,c = test()
    print(a)

import os
import sys
import getopt
import argparse


def setArgumentParser():
    algorithms = ["prlrf", "bgllrf", "adfglrf", "nlrf", "bmsnlrf"]
    scc_strategies = ["global", "local", "incremental"]
    desc = "pyRankFinder: a Ranking Function finder on python."
    argParser = argparse.ArgumentParser(description=desc)
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 4),
                           help="increase output verbosity", default=0)
    argParser.add_argument("--dotProgram", type=argparse.FileType('w'),
                           required=False,
                           help="Outfile to show the program as dot graph.")
    argParser.add_argument("-dt", "--different_template", action='store_true',
                           help="Use different templates on each node")
    argParser.add_argument("-sccs", "--scc_strategy", required=False,
                           default=scc_strategies[0], choices=scc_strategies,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-ver", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("-f", "--file", type=argparse.FileType('r'),
                           required=True, help="File to be analysed.")
    argParser.add_argument("-a", "--algorithm", choices=algorithms,
                           required=True, help="Algorithm to be apply.")
    return argParser


def Main(argv):
    argParser = setArgumentParser()
    args = argParser.parse_args(argv)
    print args
    return
    try:
        opts, args = getopt.getopt(argv, "", [])
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
    Main(sys.argv[1:])


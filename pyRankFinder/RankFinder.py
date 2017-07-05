import os
import sys
import getopt
import argparse
from TerminationAlgorithm import LRFAlgorithm
from TerminationAlgorithm import LexAlgorithm

_version = "0.0.0.1"
_name = "pyRankFinder"
_verbosity = 0


def echo(verbosity, msg):
    if _verbosity >= verbosity:
        print(msg)


def setArgumentParser():
    algorithms = ["prlrf", "bgllrf", "adfglrf", "nlrf", "bmsnlrf"]
    scc_strategies = ["global", "local", "incremental"]
    desc = _name+": a Ranking Function finder on python."
    argParser = argparse.ArgumentParser(description=desc)
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 4),
                           help="increase output verbosity", default=0)
    argParser.add_argument("--dotProgram", required=False,
                           help="Outfile to show the program as dot graph.")
    argParser.add_argument("-dt", "--different_template", action='store_true',
                           help="Use different templates on each node")
    argParser.add_argument("-sccs", "--scc_strategy", required=False,
                           default=scc_strategies[0], choices=scc_strategies,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-ver", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("-f", "--file", required=True,
                           help="File to be analysed.")
    argParser.add_argument("-a", "--algorithm", choices=algorithms,
                           required=True, help="Algorithm to be apply.")
    return argParser


def Main(argv):
    global _verbosity
    argParser = setArgumentParser()
    args = argParser.parse_args(argv)
    if args.version:
        print _name+" version: "+_version
        exit(0)
    prs = pyParser.GenericParser()
    try:
        if args.dotProgram:
            cfg = prs.parse(args.file, dot=args.dotProgram)
        else:
            cfg = prs.parse(args.file)
    except Exception as e:
        print(e)
        exit(-2)
    alg = None
    if args.algorithm == "prlrf":
        alg = LRFAlgorithm.LRFAlgorithm()
    elif args.algorithm == "adfglrf":
        alg = LexAlgorithm.LexAlgorithm()
    else:
        print("ERROR")
        exit(-1)
    
    config = vars(args)
    _verbosity = config["verbosity"]
    echo(3, config)
    config["cfg"] = cfg

    alg.print_result(alg.ranking(config))
    exit(0)

if __name__ == "__main__":
    projectPath = os.path.join(os.path.dirname(__file__), "..")
    sys.path.append(os.path.join(projectPath, "lib/pyParser/pyParser/"))
    sys.path.append(os.path.join(projectPath, "lib/pyLPi/pyLPi/"))
    globals()["pyParser"] = __import__("GenericParser")
    Main(sys.argv[1:])

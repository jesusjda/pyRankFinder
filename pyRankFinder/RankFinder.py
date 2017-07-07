import os
import sys
import getopt
import argparse
from TerminationAlgorithm import LRFAlgorithm
from TerminationAlgorithm import LexAlgorithm

_version = "0.0.0.1"
_name = "pyRankFinder"


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
    config = vars(args)
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

    Configuration = Config.the()
    Configuration.set_properties(config)
    
    alg = None
    if args.algorithm == "prlrf":
        alg = LRFAlgorithm.LRFAlgorithm()
    elif args.algorithm == "adfglrf":
        alg = LexAlgorithm.LexAlgorithm()
    else:
        print("ERROR")
        exit(-1)
    

    _verbosity = config["verbosity"]
    Configuration.echo(3, config)

    alg.print_result(alg.ranking(cfg))
    exit(0)


class Config:

    props = {}

    def __init__(self):
        if hasattr(self.__class__, 'instance'):
            raise Exception()
        self.__class__.instance = self
        # initialisation code...
        self.props = {}
        self.set_defaults()
        
    @staticmethod
    def the():
        if hasattr(Config, 'instance'):
            return Config.instance
        return Config()

    def set_properties(self, properties_dict):
        for k, v in properties_dict:
            self.props[k] = v

    def set_property(self, key, value):
        self.props[key] = value

    def get(self, key):
        return self.props[key]

    def echo(self, verbosity, msg):
        if Config.the().get("verbosity") >= verbosity:
            print(msg)
        
    
if __name__ == "__main__":
    projectPath = os.path.join(os.path.dirname(__file__), "..")
    sys.path.append(os.path.join(projectPath, "lib/pyParser/pyParser/"))
    sys.path.append(os.path.join(projectPath, "lib/pyLPi/pyLPi/"))
    globals()["pyParser"] = __import__("GenericParser")
    Main(sys.argv[1:])

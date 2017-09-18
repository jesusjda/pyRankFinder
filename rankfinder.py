import os
import sys
import getopt
import argparse
import termination
from genericparser import GenericParser
import traceback
_version = "0.0.2"
_name = "rankfinder"


def positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("Minimum value is 1")
    return ivalue


def setArgumentParser():
    algorithms = ["prlrf", "bgllrf", "adfglrf", "bmslrf", "bmsnlrf", "nlrf"]
    scc_strategies = ["global", "local", "incremental"]
    desc = _name+": a Ranking Function finder on python."
    argParser = argparse.ArgumentParser(description=desc)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 4),
                           help="increase output verbosity", default=0)
    argParser.add_argument("-ver", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("--dotDestination", required=False,
                           help="Folder to save dot graphs.")
    # Algorithm Parameters
    argParser.add_argument("-dt", "--different_template", action='store_true',
                           help="Use different templates on each node")
    argParser.add_argument("-sccd", "--scc_depth", type=positive, default=1,
                           help="Strategy based on SCC to go through the CFG.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-a", "--algorithms", choices=algorithms, nargs='+',
                           required=True, help="Algorithms to be apply.")
    return argParser


def Main(argv):
    argParser = setArgumentParser()
    args = argParser.parse_args(argv)
    config = vars(args)
    if args.version:
        print(_name + " version: " + _version)
        return
    prs = GenericParser()
    files = args.files
    for f in files:
        try:
            if args.dotDestination:
                dot = os.path.join(args.dotDestination, f + ".dot")
                cfg = prs.parse(f, dot=dot)
                os.system("xdot " + args.dotDestination + " &")
            else:
                cfg = prs.parse(f)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            return
        config["cfg"] = cfg
        internal_config = set_config(config)

        result = termination.run(internal_config)
        print(f)
        print(result)
    return


def set_config(data):
    config = {}
    if data["algorithms"] in ["adfglrf", "bgllrf"]:
        config = {
            "algorithm": "lex",
            "different_template": data["different_template"],
            "scc_depth": data["scc_depth"],
            "cfg": data["cfg"],
            "inner_alg": {
                "algorithm": data["algorithm"],
                "different_template": data["different_template"],
                "scc_depth": data["scc_depth"]
            }
        }
    elif data["algorithms"] in ["bmslrf", "bmsnlrf"]:
        config = {
            "algorithm": "bms",
            "different_template": data["different_template"],
            "scc_depth": data["scc_depth"],
            "cfg": data["cfg"],
            "inner_alg": {
                "algorithm": data["algorithm"],
                "different_template": data["different_template"],
                "scc_depth": data["scc_depth"],
                "min_depth": 1,
                "max_depth": 5
            }
        }
    else:
        config = {
            "algorithm": data["algorithms"][0],
            "different_template": data["different_template"],
            "scc_depth": data["scc_depth"],
            "cfg": data["cfg"]
        }
    return config


if __name__ == "__main__":
    Main(sys.argv[1:])

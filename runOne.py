import os
import sys
import traceback
import getopt
import argparse
import termination
from genericparser import GenericParser

_version = "0.1"
_name = "runOne"


def setArgumentParser():
    algorithms = ["pr", "bg", "adfg", "lex_bg", "lex_adfg",
                  "bms_lrf", "bms_nlrf", "nlrf"]
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

    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="Files to be analysed.")
    argParser.add_argument("-a", "--algorithm", choices=algorithms,
                           required=True, help="Algorithm to be apply.")
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
        config["transitions"] = cfg.get_edges()
        internal_config = set_config(config)

        result = termination.run(internal_config)
        print(f)
        print(result)
    return


def set_config(data):
    algs = data["algorithm"].split('_')
    dt = data["different_template"]
    trans = data["transitions"]
    inner_alg = None
    config = {}
    for alg in reversed(algs):
        config = {
            "algorithm": alg,
            "different_template": dt,
            "transitions": trans
        }
        if not (inner_alg is None):
            config["inner_alg"] = inner_alg
            if alg == "bms":
                config["inner_alg"]["min_depth"] = 1
                config["inner_alg"]["max_depth"] = 5
        if alg == "nlrf":
            config["min_depth"] = 1
            config["max_depth"] = 5
        if alg == "lrf":
            config["min_depth"] = 1
            config["max_depth"] = 1

        inner_alg = config
    return config

if __name__ == "__main__":
    Main(sys.argv[1:])

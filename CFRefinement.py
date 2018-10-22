import os
import sys
import argparse
import genericparser
from termination import Output_Manager as OM
from irankfinder import control_flow_refinement

_version = "1.0"
_name = "CFRefinement"

def setArgumentParser():
    desc = _name+": Control Flow refinement."
    argParser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawTextHelpFormatter)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    argParser.add_argument("-V", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
    argParser.add_argument("-of", "--output_formats", required=False, nargs='+',
                           choices=["fc", "dot", "koat", "pl", "svg"], default=["fc", "dot", "svg"],
                           help="Formats to print the graphs.")
    argParser.add_argument("-od", "--output-destination", required=False,
                           help="Folder to save output files.")
    # CFR Parameters
    argParser.add_argument("-cfr-au", "--cfr-automatic-properties", required=False,
                           type=int, choices=range(0,5), default=4,
                           help="")
    argParser.add_argument("-cfr-it", "--cfr-iterations", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=1)
    argParser.add_argument("-cfr-it-st", "--cfr-iteration-strategy", required=False,
                           choices=["acumulate", "inmutate", "recompute"], default="recompute",
                           help="")
    argParser.add_argument("-cfr-usr", "--cfr-user-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-inv", "--cfr-invariants", required=False,
                           default="none", help="CFR with Invariants.")
    argParser.add_argument("-cfr-sc", "--cfr-simplify-constraints", required=False,
                           default=False, action='store_true',
                           help="Simplify constraints when CFR")
    argParser.add_argument("-cfr-inv-thre", "--cfr-invariants-threshold", required=False,
                           default=False, action='store_true',
                           help="Use user thresholds for CFR invariants.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("--tmpdir", required=False, default=None,
                           help="Temporary directory.")
    return argParser

def extractname(filename):
    f = os.path.split(filename)
    b = os.path.split(f[0])
    c = os.path.splitext(f[1])
    return os.path.join(b[1], c[0])

def launch(config):
    for f in config["files"]:
        launch_file(config, f)
        OM.show_output()

def launch_file(config, f):
    try:
        config["name"] = extractname(f)
        control_flow_refinement(genericparser.parse(f), config,
                                au_prop=config["cfr_automatic_properties"],
                                console=True, writef=True)

    except Exception as e:
        OM.printf("Exception  -> "+str(e))
        raise Exception() from e

if __name__ == "__main__":
    try:
        argv = sys.argv[1:]
        argParser = setArgumentParser()
        args = argParser.parse_args(argv)
        OM.restart(verbosity=args.verbosity, ei=args.ei_out)
        if args.version:
            print(_name + " version: " + _version)
            exit(0)
        config = vars(args)
        launch(config)
    except Exception as e:
        OM.show_output()
        raise Exception() from e


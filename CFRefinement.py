import os
import sys
import argparse
import genericparser
from termination import Output_Manager as OM
from partialevaluation import control_flow_refinement
from nodeproperties import compute_invariants
from termination.algorithm.utils import showgraph

_version = "1.2"
_name = "CFRefinement"

def setArgumentParser():
    desc = _name+": Control Flow refinement."
    absdomains = ["none", "interval", "polyhedra"]
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
    argParser.add_argument("-si", "--show-with-invariants", required=False, default=False,
                           action='store_true', help="add invariants to the output formats")
    
    # CFR Parameters
    argParser.add_argument("-cfr-au", "--cfr-automatic-properties", required=False,
                           type=int, choices=range(0,5), default=4, help="")
    argParser.add_argument("-cfr-it", "--cfr-iterations", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=1)
    # argParser.add_argument("-cfr-it-st", "--cfr-iteration-strategy", required=False,
    #                       choices=["acumulate", "inmutate", "recompute"], default="recompute",
    #                       help="")
    argParser.add_argument("-cfr-usr", "--cfr-user-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-inv", "--cfr-invariants", required=False, choices=absdomains,
                           default="none", help="CFR with Invariants.")
    argParser.add_argument("-i", "--invariants", required=False, choices=absdomains,
                           default="none", help="Compute Invariants.")
    argParser.add_argument("-ithre", "--invariants-threshold", required=False,
                           action='store_true', help="Use user thresholds.")
    argParser.add_argument("-cfr-sc", "--cfr-simplify-constraints", required=False,
                           default=False, action='store_true',
                           help="Simplify constraints when CFR")
    argParser.add_argument("-cfr-inv-thre", "--cfr-invariants-threshold", required=False,
                           default=False, action='store_true',
                           help="Use user thresholds for CFR invariants.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("--tmpdir", required=False, default="/tmp",
                           help="Temporary directory.")
    return argParser

def extractname(filename):
    f = os.path.split(filename)
    c = os.path.splitext(f[1])
    return c[0]

def launch(config):
    for f in config["files"]:
        launch_file(config, f)
        OM.show_output()

def launch_file(config, f):
    writef = config["output_destination"] is not None
    console = not writef or config["ei_out"]
    try:
        config["name"] = extractname(f)
        pe_cfg = control_flow_refinement(genericparser.parse(f), config,
                                         console=console, writef=writef)
        if config["invariants"] != "none":
            config["show_with_invariants"] = True
            compute_invariants(pe_cfg, abstract_domain=config["invariants"],
                               use_threshold=config["invariants_threshold"])
            if config["cfr_iterations"] > 0:
                sufix = "_cfr"+str(config["cfr_iterations"])
            sufix += "_with_inv"+str(config["invariants"])
            showgraph(pe_cfg, config, sufix=sufix, invariant_type=config["invariants"], console=console, writef=writef)
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


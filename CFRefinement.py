import os
import sys
import argparse
import genericparser
from termination import Output_Manager as OM
from partialevaluation import control_flow_refinement
from nodeproperties import invariant
from termination.algorithm.utils import showgraph

_version = "1.2"
_name = "CFRefinement"


def threshold_type(value):
    from nodeproperties.thresholds import threshold_options
    if value in threshold_options():
        return value
    raise argparse.ArgumentTypeError("{} is not a valid threshold mode.".format(value))


def setArgumentParser():
    desc = _name + ": Control Flow refinement."
    absdomains = ["none", "interval", "polyhedra"]
    output_formats = ["fc", "dot", "svg", "koat", "pl", "smt2"]
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
    argParser.add_argument("-of", "--output-formats", required=False, nargs='+',
                           choices=output_formats, default=output_formats[:3],
                           help="Formats to print the graphs.")
    argParser.add_argument("-od", "--output-destination", required=False,
                           help="Folder to save output files.")
    argParser.add_argument("-si", "--show-with-invariants", required=False, default=False,
                           action='store_true', help="add invariants to the output formats")
    # CFR Parameters
    argParser.add_argument("-cfr-usr", "--cfr-user-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-cone", "--cfr-cone-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-head", "--cfr-head-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-head-var", "--cfr-head-var-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-call", "--cfr-call-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-call-var", "--cfr-call-var-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-head-deep", "--cfr-head-deep-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-split", "--cfr-split-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-it", "--cfr-iterations", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=1)

    argParser.add_argument("-cfr-inv", "--cfr-invariants", action='store_true',
                           default="none", help="CFR with Invariants.")
    argParser.add_argument("-cfr-nodes", "--cfr-nodes", required=False, nargs="*",
                           default=[], help=".")
    argParser.add_argument("-cfr-nodes-mode", "--cfr-nodes-mode", required=False,
                           default="all", choices=["john", "cyclecutnodes", "all", "user"], help=".")
    argParser.add_argument("-i", "--invariants", required=False, choices=absdomains,
                           default="none", help="Compute Invariants.")
    argParser.add_argument("-inv-thre", "--invariants-threshold", required=False, default=[], nargs="+",
                           type=threshold_type, help="Use thresholds.")
    argParser.add_argument("-inv-wide-nodes", "--invariant-widening-nodes", required=False, nargs="*",
                           default=[], help=".")
    argParser.add_argument("-inv-wide-nodes-mode", "--invariant-widening-nodes-mode", required=False,
                           default="all", choices=["cyclecutnodes", "all", "user"], help=".")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--file", required=True, help="File to be analysed.")
    argParser.add_argument("--tmpdir", required=False, default="/tmp",
                           help="Temporary directory.")
    return argParser


def extractname(filename):
    f = os.path.split(filename)
    c = os.path.splitext(f[1])
    return c[0]


def launch(config):
    f = config["file"]
    writef = config["output_destination"] is not None
    console = not writef or config["ei_out"]
    invariant.set_configuration(config)
    sufix = ""
    try:
        config["name"] = extractname(f)
        cfg = genericparser.parse(f)
        cfg.build_polyhedrons()
        invariant.compute_invariants(cfg, add_to_polyhedron=True)
        pe_cfg = control_flow_refinement(cfg, config,
                                         console=console, writef=writef)
        if config["invariants"] != "none":
            config["show_with_invariants"] = True
            invariant.compute_invariants(pe_cfg, add_to_polyhedron=True)
            if config["cfr_iterations"] > 0:
                sufix += "_cfr" + str(config["cfr_iterations"])
            sufix += "_with_inv" + str(config["invariants"])
            showgraph(pe_cfg, config, sufix=sufix, invariant_type=config["invariants"], console=console, writef=writef)
        OM.show_output()
    except Exception as e:
        OM.printf("Exception  -> " + str(e))
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

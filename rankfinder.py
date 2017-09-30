import os
import sys
import traceback
import getopt
import argparse
import termination
from genericparser import GenericParser

_version = "0.0.2"
_name = "rankfinder"


def positive(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("Minimum value is 0")
    return ivalue


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
    argParser.add_argument("-sccd", "--scc_depth", type=positive, default=0,
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
        config["vars_name"] = cfg.get_var_name()
        result = rank(config, [(cfg, config["scc_depth"])], config["algorithms"])
        print(f)
        print(result)
    return


def rank(config, CFGs, algs):
    rfs = []
    while (CFGs):
        current_cfg, sccd = CFGs.pop(0)
        if sccd > 0:
            CFGs_aux = current_cfg.get_sccs()
        else:
            CFGs_aux = [current_cfg]
        for cfg in CFGs_aux:
            Trans = cfg.get_edges()
            R = run_algs(config, Trans, algs)
            if not R.found():
                raise Exception("NOT FOUND")
            rfs.append(R.get("rfs"))
            pending_trs = R.get("pending_trs")
            if pending_trs:
                if sccd > 0:
                    CFGs = [(Cfg(pending_trs, cfg.get_var_name()),
                             sccd-1)] + CFGs
                else:
                    raise Exception("NOT FOUND")
    return rfs


def run_algs(config, trans, algs):
    response = termination.Result()
    R = None
    f = False
    for alg in algs:
        internal_config = set_config(config, alg, trans)

        R = termination.run(internal_config)
        if R.found():
            if R.get("rfs"):
                f = True
                break

    if f:
        pen = R.get("pending_trs")
        response.set_response(found=True,
                              info="Found",
                              rfs=R.get("rfs"),
                              pending_trs=pen)
        return response

    response.set_response(found=False,
                          info="Not Found")
    return response


def set_config(data, alg, trans):
    algs = alg.split('_')
    dt = data["different_template"]

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
        inner_alg = config

    return config

if __name__ == "__main__":
    Main(sys.argv[1:])

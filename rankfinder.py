import os
import sys
import traceback
import getopt
import argparse
import termination
from termination.output import Output_Manager as OM
from genericparser import GenericParser
from genericparser.Cfg import Cfg

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
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
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
    OM.verbosity = args.verbosity
    OM.ei = args.ei_out
    if args.version:
        print(_name + " version: " + _version)
        return
    config = vars(args)
    prs = GenericParser()
    files = args.files

    for f in files:
        aux_p = f.split('/')
        aux_c = len(aux_p) - 1
        while aux_c > 0:
            if aux_p[aux_c] == "examples":
                break
            if aux_p[aux_c] == "User_Projects":
                break
            aux_c -= 1
        r = '/'.join(aux_p[aux_c:])

        OM.restart(dest=r)
        OM.show_output()
        try:
            if args.dotDestination:
                s = r.replace('/', '_')
                dot = os.path.join(args.dotDestination, s + ".dot")
                OM.printif(2, dot)
                cfg = prs.parse(f, dotgraph=dot)
                # os.system("xdot " + args.dotDestination + " &")
            else:
                cfg = prs.parse(f)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            return
        config["vars_name"] = cfg.get_var_name()
        result = rank(config, [(cfg, config["scc_depth"])],
                      config["algorithms"])
        OM.printif(1, f)
        OM.printif(0, result.toString(cfg.get_var_name()))
        tr_rfs = result.get("tr_rfs")
        OM.printf(tr_rfs)
        for tr in tr_rfs:
            OM.print_rf_tr(cfg, tr, tr_rfs[tr])
        OM.show_output()
    return


def rank(config, CFGs, algs):
    response = termination.Result()
    rfs = {}
    tr_rfs = {}
    fail = False
    while (not fail and CFGs):
        current_cfg, sccd = CFGs.pop(0)
        if sccd > 0:
            CFGs_aux = current_cfg.get_sccs()
        else:
            CFGs_aux = [current_cfg]
        for cfg in CFGs_aux:
            Trans = cfg.get_edges()
            if len(Trans) < 1:
                continue
            R = run_algs(config, algs, Trans, cfg.get_var_name())
            if not R.found():
                fail = True
                break
            merge_rfs(rfs, R.get("rfs"))
            merge_rfs(tr_rfs, R.get("tr_rfs"))
            pending_trs = R.get("pending_trs")
            if pending_trs:
                CFGs = [(Cfg(pending_trs, cfg.get_var_name()),
                         sccd)] + CFGs
    if fail:
        response.set_response(found=False)
    else:
        response.set_response(found=True)
    response.set_response(rfs=rfs,
                          tr_rfs=tr_rfs,
                          pending_cfgs=CFGs)
    return response


def run_algs(config, algs, trans, vars_name):
    response = termination.Result()
    R = None
    f = False
    trs = ""
    for t in trans:
        trs += t["name"]+","
    OM.printif(1, "Analyzing transitions: "+trs)
           
    for alg in algs:
        internal_config = set_config(config, alg, trans)
        try:
            OM.printif(1, "-> with: " + alg)
            R = termination.run(internal_config)
            OM.printif(2, R.debug())
            OM.printif(1, R.toString(vars_name))
            if R.found():
                if R.get("rfs"):
                    f = True
                    break
        except:
            pass

    if f:
        pen = R.get("pending_trs")
        response.set_response(found=True,
                              info="Found",
                              rfs=R.get("rfs"),
                              tr_rfs=R.get("tr_rfs"),
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
        if alg == "nlrf":
            config["min_depth"] = 1
            config["max_depth"] = 5
        if not (inner_alg is None):
            config["inner_alg"] = inner_alg

        inner_alg = config

    return config


def merge_rfs(rfs, to_add):
    new_rfs = rfs
    for key in to_add:
        if key in new_rfs:
            if not isinstance(new_rfs[key], list):
                new_rfs[key] = [new_rfs[key]]
            new_rfs[key].append(to_add[key])
        else:
            new_rfs[key] = to_add[key]
    return new_rfs

if __name__ == "__main__":
    Main(sys.argv[1:])

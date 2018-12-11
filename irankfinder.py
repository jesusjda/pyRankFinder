import argparse
import nodeproperties
import os
import sys
from termination import Termination_Algorithm_Manager as TAM
from termination import NonTermination_Algorithm_Manager as NTAM
from termination import Output_Manager as OM
import termination
from partialevaluation import partialevaluate
import cProfile
# from termination.profiler import register_as

def do_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            #profile.print_stats('time', 'name')
            profile.print_stats('launch_file')
    return profiled_func

_version = "1.0"
_name = "irankfinder"


def positive(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("Minimum value is 0")
    return ivalue


def termination_alg(value):
    if value == "none":
        return None
    try:
        return TAM.get_algorithm(value)
    except ValueError:
        raise argparse.ArgumentTypeError("{} is not a valid termination algorithm.".format(value))


def termination_alg_desc():
    return ("Algorithms allowed:\n\t"
            + "\n\t".join(TAM.options(True)))


def nontermination_alg(value):
    if value == "none":
        return None
    try:
        return NTAM.get_algorithm(value)
    except ValueError:
        raise argparse.ArgumentTypeError("{} is not a valid termination algorithm.".format(value)) 


def nontermination_alg_desc():
    return ("Algorithms allowed:\n\t"
            + "\n\t".join(NTAM.options(True)))


def setArgumentParser():
    desc = _name+": a Ranking Function finder on python."
    dt_options = ["never", "iffail", "always"]
    absdomains = ["none", "interval", "polyhedra"]
    argParser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawTextHelpFormatter)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    argParser.add_argument("-V", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("-od", "--output-destination", required=False,
                           help="Folder to save output files.")
    argParser.add_argument("-of", "--output-formats", required=False, nargs='+',
                           choices=["fc", "dot", "koat", "pl", "svg"], default=["fc", "dot", "svg"],
                           help="Formats to print the graphs.")
    argParser.add_argument("-si", "--show-with-invariants", required=False, default=False,
                           action='store_true', help="add invariants to the output formats")
    argParser.add_argument("--tmpdir", required=False, default="",
                           help="Temporary directory.")
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
    argParser.add_argument("--print-graphs", required=False, action='store_true',
                           help="Shows the output in fc and svg format")
    # Algorithm Parameters
    argParser.add_argument("-dt", "--different-template", required=False,
                           choices=dt_options, default=dt_options[0],
                           help="Use different templates on each node")
    argParser.add_argument("-sccd", "--scc-depth", type=positive, default=1,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-sc", "--simplify-constraints", required=False,
                           default=False, action='store_true',
                           help="Simplify constraints")
    argParser.add_argument("-usr-reach", "--user-reachability", required=False,
                           default=False, action='store_true',
                           help="Compute reachability from user constraints")
    argParser.add_argument("-reach", "--reachability", required=False, choices=absdomains,
                           default="none", help="Analyse reachability")
    argParser.add_argument("-rniv", "--remove-no-important-variables", required=False,
                           default=False, action='store_true',
                           help="Remove No Important variables before do anything else.")
    argParser.add_argument("-lib", "--lib", required=False, choices=["ppl", "z3"],
                           default="z3", help="select lib")
    # CFR Parameters
    argParser.add_argument("-cfr-au", "--cfr-automatic-properties", required=False,
                           type=int, choices=range(0,5), default=4,
                           help="")
    argParser.add_argument("-cfr-it", "--cfr-iterations", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=0)
    argParser.add_argument("-cfr-mx-t", "--cfr-max-tries", type=int, choices=range(0, 5),
                           help="max tries to apply cfr on scc level", default=4)
    argParser.add_argument("-cfr-st-before", "--cfr-strategy-before", action='store_true',
                           help="")
    argParser.add_argument("-cfr-st-scc", "--cfr-strategy-scc", action='store_true',
                           help="")
    argParser.add_argument("-cfr-st-after", "--cfr-strategy-after", action='store_true',
                           help="")
    argParser.add_argument("-cfr-usr", "--cfr-user-properties", action='store_true',
                           help="")
    argParser.add_argument("-cfr-inv", "--cfr-invariants", required=False, choices=absdomains,
                           default="none", help="CFR with Invariants.")
    argParser.add_argument("-cfr-sc", "--cfr-simplify-constraints", required=False,
                           default=False, action='store_true',
                           help="Simplify constraints when CFR")
    argParser.add_argument("-cfr-inv-thre", "--cfr-invariants-threshold", required=False,
                           default=False, action='store_true',
                           help="Use user thresholds for CFR invariants.")
    argParser.add_argument("-rec-set", "--recurrent-set", required=False,
                           help="File where print, on certain format, sccs that we don't know if terminate.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-nt", "--nontermination", type=nontermination_alg,
                           nargs='*', required=False, default=[],
                           help=nontermination_alg_desc())
    argParser.add_argument("-t", "--termination", type=termination_alg, default=[],
                           nargs='*', required=False,
                           help=termination_alg_desc())
    argParser.add_argument("-ct", "--conditional-termination", required=False,
                           default=False, action='store_true',
                           help="Do conditional temination over the nodes where we cannot proof termination.")
    argParser.add_argument("-i", "--invariants", required=False, choices=absdomains,
                           default="none", help="Compute Invariants.")
    argParser.add_argument("-ithre", "--invariants-threshold", required=False,
                           action='store_true', help="Use user thresholds.")
    argParser.add_argument("-sif", "--stop-if-fail", required=False,
                           default=False, action='store_true',
                           help="If an SCC fails the analysis will stop.")
    return argParser


def extractname(filename):
    f = os.path.split(filename)
    b = os.path.split(f[0])
    c = os.path.splitext(f[1])
    return os.path.join(b[1], c[0])

def launch(config):
    files = config["files"]
    if "outs" in config:
        outs = config["outs"]
    else:
        outs = []
    for i in range(len(files)):
        if(len(files) > 1):
            OM.printf(files[i])
        if len(outs) <= i:
            o = None
        else:
            o = outs[i]
        config["name"] = extractname(files[i])
        launch_file(config, files[i], o)


def parse_file(f):
    import genericparser
    return genericparser.parse(f)

def launch_file(config, f, out):
    aux_p = f.split('/')
    aux_c = len(aux_p) - 1
    while aux_c > 0:
        if aux_p[aux_c] == "examples":
            break
        if aux_p[aux_c] == "User_Projects":
            break
        aux_c -= 1
    r = None
    try:
        cfg = parse_file(f)
    except Exception as e:
        OM.restart(odest=out, cdest=r, vars_name=[])
        if out is not None:
            tmpfile = os.path.join(os.path.curdir, out)
            with open(tmpfile, "w") as f:
                f.write(e)
        else:
            OM.printerrf("Parser Error: {}\n{}".format(type(e).__name__, str(e)))
        return
    OM.restart(odest=out, cdest=r)
    remove_no_important_variables(cfg, doit=config["remove_no_important_variables"])
    OM.show_output()

    config["vars_name"] = cfg.get_info("global_vars")
    OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    if config["user_reachability"]:
        cfg.build_polyhedrons()
        compute_reachability(cfg, abstract_domain="polyhedra", use=config["user_reachability"], user_props=True,
                             use_threshold=config["invariants_threshold"])
        return None
    # Compute Termination
    termination_result = analyse(config, cfg)
    show_result(termination_result, cfg)
    OM.show_output()
    OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    from termination.algorithm.utils import showgraph
    showgraph(cfg, config, sufix="_node_notes_added", invariant_type=config["invariants"], console=config["print_graphs"], writef=False, output_formats=["fc"])
    return termination_result

def remove_no_important_variables(cfg, doit=False):
    if not doit:
        return
    cons, nivars = cfg.remove_no_important_variables()
    OM.printif(1, "Removed {} constraint(s) with variable(s): [{}]".format(cons, ",".join(nivars)))

def analyse(config, cfg):
    OM.printseparator(1)
    r = termination.analyse(config, cfg)
    if r.get_status().is_terminate():
        return r
    if r.has("unknown_sccs"):
        unk_sccs = r.get("unknown_sccs")
        if r.has("graph"):
            graph = r.get("graph")
        else:
            graph = cfg
    else:
        return r

    # from here all is experimental. This doesn't produce termination results.
    if config["conditional_termination"] and len(unk_sccs) > 0:
        # analyse reachability for all the nodes where we don't prove termination
        OM.printseparator(0)
        OM.printf("Conditional termination (negation of the following conditions) (',' means 'and')")
        nodes_to_analyse = []
        for scc in unk_sccs:
            nodes_to_analyse += scc.get_nodes()
        if len(nodes_to_analyse) == 0:
            OM.printf("No nodes to analyse reachability.")
        else:
            compute_reachability(graph,use=False, init_nodes=nodes_to_analyse)
        OM.printseparator(0)
    elif "recurrent_set" in config and config["recurrent_set"] and len(unk_sccs) > 0:
        OM.printseparator(0)
        count = 0
        for scc in unk_sccs:
            scc.toEspecialProlog(config["recurrent_set"], count, config["name"])
            count += 1
        OM.printseparator(0)
    return r

def show_result(result, cfg):
    OM.printseparator(1)
    OM.printf(result.toString(cfg.get_info("global_vars")))

    no_lin = [tr["name"] for tr in cfg.get_edges() if not tr["linear"]]
    if no_lin:
        OM.printif(1, "Removed no linear constraints from transitions: " +
                   str(no_lin))
    OM.printseparator(1)


def compute_reachability(cfg, abstract_domain="polyhedra", use=True, use_threshold=False, user_props=False, init_nodes=[]):
    cfg.build_polyhedrons()
    node_inv = nodeproperties.compute_reachability(cfg, abstract_domain, use_threshold=use_threshold, user_props=user_props, init_nodes=init_nodes)
    if use:
        OM.printseparator(0)
        OM.printf("REACHABILITY ({})".format(abstract_domain))
    gvars = cfg.get_info("global_vars")
    OM.printf("\n".join(["-> " + str(n) + " = " +
                         str(node_inv[n].toString(gvars))
                         for n in sorted(node_inv)]))
    if use:
        OM.printseparator(0)


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
        if "termination" in config and config["termination"] is not None:
            config["termination"] = [alg for alg in config["termination"] if alg is not None]
        if "nontermination" in config and config["nontermination"] is not None:
            config["nontermination"] = [alg for alg in config["nontermination"] if alg is not None]
        if config["cfr_strategy_scc"] and config["cfr_strategy_after"]:
            raise argparse.ArgumentTypeError("CFR strategies `scc` and `after` can not be applied together.")
        launch(config)
    finally:
        OM.show_output()

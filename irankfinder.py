import argparse
import nodeproperties
import os
import sys
from termination import Termination_Algorithm_Manager as TAM
from termination import NonTermination_Algorithm_Manager as NTAM
from termination import Output_Manager as OM
from termination.algorithm.utils import showgraph


_version = "1.1"
_name = "irankfinder"


def positive(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("Minimum value is 0")
    return ivalue


def threshold_type(value):
    from nodeproperties.thresholds import threshold_options
    if value in threshold_options():
        return value
    raise argparse.ArgumentTypeError("{} is not a valid threshold mode.".format(value))


def termination_alg(value):
    if value == "none":
        return None
    try:
        return TAM.get_algorithm(value)
    except ValueError:
        raise argparse.ArgumentTypeError("{} is not a valid termination algorithm.".format(value))


def termination_alg_desc():
    return ("Algorithms allowed:\n\t" +
            "\n\t".join(TAM.options(True)))


def nontermination_alg(value):
    if value == "none":
        return None
    try:
        return NTAM.get_algorithm(value)
    except ValueError:
        raise argparse.ArgumentTypeError("{} is not a valid termination algorithm.".format(value))


def nontermination_alg_desc():
    return ("Algorithms allowed:\n\t" +
            "\n\t".join(NTAM.options(True)))


def setCFRArgumentsParser(group):
    group.add_argument("-cfr-it", "--cfr-iterations", type=int, choices=range(0, 5),
                       help="# times to apply cfr", default=0)
    group.add_argument("-cfr-mx-t", "--cfr-max-tries", type=int, choices=range(0, 5),
                       help="max tries to apply cfr on scc level", default=4)
    group.add_argument("-cfr-st-before", "--cfr-strategy-before", action='store_true',
                       help="")
    group.add_argument("-cfr-st-scc", "--cfr-strategy-scc", action='store_true',
                       help="")
    group.add_argument("-cfr-st-after", "--cfr-strategy-after", action='store_true',
                       help="")
    group.add_argument("-cfr-usr", "--cfr-user-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-cone", "--cfr-cone-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-head", "--cfr-head-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-head-var", "--cfr-head-var-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-call", "--cfr-call-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-call-var", "--cfr-call-var-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-head-deep", "--cfr-head-deep-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-split", "--cfr-split-properties", action='store_true',
                       help="")
    group.add_argument("-cfr-inv", "--cfr-invariants", action='store_true',
                       help="CFR with Invariants.")
    group.add_argument("-cfr-nodes", "--cfr-nodes", required=False, nargs="*",
                       default=[], help=".")
    group.add_argument("-cfr-nodes-mode", "--cfr-nodes-mode", required=False,
                       default="all", choices=["john", "cyclecutnodes", "all", "user"], help=".")


def setArgumentParser():
    desc = _name + ": a Ranking Function finder on python."
    dt_options = ["never", "iffail", "always"]
    domains = ["Z", "Q", "user"]
    dt_scheme_options = ["default", "inhomogeneous"]
    absdomains = ["none", "interval", "polyhedra"]
    output_formats = ["fc", "dot", "svg", "koat", "pl", "smt2"]
    argParser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawTextHelpFormatter)
    setCFRArgumentsParser(argParser.add_argument_group('cfr', "CFR parameters"))
    # Output Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    argParser.add_argument("-V", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("-od", "--output-destination", required=False,
                           help="Folder to save output files.")
    argParser.add_argument("-of", "--output-formats", required=False, nargs='+',
                           choices=output_formats, default=output_formats[:3],
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
    argParser.add_argument("-d", "--domain", required=False,
                           choices=domains, default=domains[0],
                           help="Domain of the variables")
    argParser.add_argument("-dt", "--different-template", required=False,
                           choices=dt_options, default=dt_options[0],
                           help="Use different templates on each node")
    argParser.add_argument("-dt-scheme", "--different-template-scheme", required=False,
                           choices=dt_scheme_options, default=dt_scheme_options[0],
                           help="Use different templates on each node")
    argParser.add_argument("-sccd", "--scc-depth", type=positive, default=5,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-usr-reach", "--user-reachability", required=False,
                           default=False, action='store_true',
                           help="Compute reachability from user constraints")
    argParser.add_argument("-reach", "--reachability", required=False, choices=absdomains,
                           default="polyhedra", help="Analyse reachability")
    argParser.add_argument("-rniv", "--remove-no-important-variables", required=False,
                           default=False, action='store_true',
                           help="Remove No Important variables before do anything else.")
    argParser.add_argument("-ca", "--check-assertions", action='store_true',
                           help="Check Invariants with the assertions defined")
    argParser.add_argument("-rfs-as-cfr-props", "--rfs-as-cfr-props", action='store_true',
                           help="Print a graph with rfs as user props.")
    argParser.add_argument("-scc-pl", "--print-scc-prolog", required=False,
                           help="File where print, on certain format, sccs that we don't know if terminate.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--file", required=True, help="File to be analysed.")
    argParser.add_argument("-cfgpf", "--cfg-properties-file", required=False,
                           help="File with the properties of nodes.")
    argParser.add_argument("-nt", "--nontermination", type=nontermination_alg,
                           nargs='*', required=False, default=[],
                           help=nontermination_alg_desc())
    argParser.add_argument("-nt-reach", "--nt-reachability", required=False,
                           default=False, action='store_true',
                           help="Analyse reachability when NT algorithms says NO.")
    argParser.add_argument("-t", "--termination", type=termination_alg, default=[],
                           nargs='*', required=False,
                           help=termination_alg_desc())
    argParser.add_argument("-ct", "--conditional-termination", required=False,
                           default=False, action='store_true',
                           help="Do conditional termination over the nodes where we cannot proof termination.")
    argParser.add_argument("-i", "--invariants", required=False, choices=absdomains,
                           default="none", help="Compute Invariants.")
    argParser.add_argument("-inv-wide-nodes", "--invariant-widening-nodes", required=False, nargs="*",
                           default=[], help=".")
    argParser.add_argument("-inv-wide-nodes-mode", "--invariant-widening-nodes-mode", required=False,
                           default="all", choices=["cyclecutnodes", "all", "user"], help=".")
    argParser.add_argument("-inv-thre", "--invariants-threshold", required=False, default=[], nargs="+",
                           type=threshold_type, help="Use thresholds.")
    argParser.add_argument("-sif", "--stop-if-fail", required=False,
                           default=False, action='store_true',
                           help="If an SCC fails the analysis will stop.")
    return argParser


def extractname(filename):
    f = os.path.split(filename)
    b = os.path.split(f[0])
    c = os.path.splitext(f[1])
    return os.path.join(b[1], c[0])


def parse_file(f, cfgpf=None):
    try:
        import genericparser
        cfg = genericparser.parse(f)
        if cfgpf is not None:
            genericparser.parse_cfg_props(cfgpf, cfg)
        return cfg
    except Exception as e:
        OM.restart(vars_name=[])
        OM.printerrf("Parser Error: {}\n{}".format(type(e).__name__, str(e)))
        raise Exception() from e
        return None


def launch(config):
    f = config["file"]
    cfgpf = config["cfg_properties_file"]
    config["name"] = extractname(f)
    cfg = parse_file(f, cfgpf)
    if cfg is None:
        return
    if "domain" in config and config["domain"] == "user":
        config["domain"] = cfg.get_info("domain")
    nodeproperties.invariant.set_configuration(config)
    OM.restart()
    remove_no_important_variables(cfg, doit=config["remove_no_important_variables"])
    OM.show_output()
    config["vars_name"] = cfg.get_info("global_vars")
    OM.restart(vars_name=config["vars_name"])
    # Rechability
    compute_reachability(cfg, abstract_domain=config["reachability"], do=config["user_reachability"], user_props=True,
                         threshold_modes=config["invariants_threshold"])
    # Assertions
    check_assertions(config, cfg)

    # Compute Termination
    termination_result = analyse(config, cfg)
    # Post analyses
    if termination_result.has("unknown_sccs"):
        unk_sccs = termination_result.get("unknown_sccs")
        if termination_result.has("graph"):
            graph = termination_result.get("graph")
        else:
            graph = cfg
        # from here all is experimental. This doesn't produce termination results.
        conditional_termination(config, graph, unk_sccs)
        print_scc_prolog(config, unk_sccs)
    # Show
    OM.show_output()
    OM.restart(vars_name=config["vars_name"])
    showgraph(cfg, config, sufix="_node_notes_added", invariant_type=config["invariants"], console=config["print_graphs"],
              writef=False, output_formats=["fc"])
    return termination_result


def remove_no_important_variables(cfg, doit=False):
    if not doit:
        return
    cons, nivars = cfg.remove_no_important_variables()
    OM.printif(1, "Removed {} constraint(s) with variable(s): [{}]".format(cons, ",".join(nivars)))


def analyse(config, cfg):
    import termination
    r = termination.analyse(config, cfg)
    show_result(r, cfg)
    rfs_as_cfr_props(config, cfg, r)
    return r


def rfs_as_cfr_props(config, cfg, result):
    if not config.get("rfs_as_cfr_props", False):
        return
    if not result.has("rfs") or len(result.get("rfs").keys()) == 0:
        showgraph(cfg, config, sufix="_rfs_as_cfr", invariant_type=config["invariants"], console=config["print_graphs"],
                  writef=True, output_formats=["fc"])
        OM.printf("ERROR: no rfs to use as cfr props")
        return
    from lpi.expressions import Expression
    rfs = result.get("rfs")

    def toconstraint(cs):
        if isinstance(cs, Expression):
            return [[cs >= 0], [cs < 0]]
        sol = []
        for c in cs:
            sol += toconstraint(c)
        return sol
    props = {n: toconstraint(rfs[n]) for n in rfs}
    cfg.set_nodes_info(props, "cfr_rfs_properties")
    showgraph(cfg, config, sufix="_rfs_as_cfr", invariant_type=config["invariants"], console=config["print_graphs"],
              writef=True, output_formats=["fc"])


def show_result(result, cfg):
    OM.printseparator(1)
    OM.printf(result.toString(cfg.get_info("global_vars")))

    no_lin = [tr["name"] for tr in cfg.get_edges() if not tr["linear"]]
    if no_lin:
        OM.printif(1, "Removed no linear constraints from transitions: " +
                   str(no_lin))
    OM.printseparator(1)


def check_assertions(config, cfg):
    if not config.get("check_assertions", False):
        return
    elif config["invariants"] == "none":
        OM.printf("ERROR: Please select an abstract domain for invariants.")
        return
    OM.printf("Computing and checking invariants...")
    nodeproperties.invariant.compute_invariants(cfg, check=True, add_to_polyhedron=False)
    showgraph(cfg, config, sufix="", console=config["print_graphs"], writef=False, output_formats=["fc", "svg"])
    if config["cfr_strategy_before"]:
        OM.printf("Refining graph...")
        from partialevaluation import control_flow_refinement
        cfg = control_flow_refinement(cfg, config)
        cfg.remove_unsat_edges()
        OM.printf("Computing and checking invariants...")
        nodeproperties.invariant.compute_invariants(cfg, check=True, add_to_polyhedron=False)
        showgraph(cfg, config, sufix="cfr_before", console=config["print_graphs"], writef=False, output_formats=["fc", "svg"])


def conditional_termination(config, cfg, unk_sccs):
    if not config.get("conditional_termination", False):
        return
    if len(unk_sccs) == 0:
        OM.printf("No pending sccs to analyse conditional termination")
        return
    # analyse reachability for all the nodes where we don't prove termination
    OM.printseparator(0)
    OM.printf("Conditional termination (negation of the following conditions) (',' means 'and')")
    nodes_to_analyse = []
    for scc in unk_sccs:
        nodes_to_analyse += scc.get_nodes()
    if len(nodes_to_analyse) == 0:
        OM.printf("No nodes to analyse reachability.")
    else:
        compute_reachability(cfg, threshold_modes=config["invariants_thresholds"], init_nodes=nodes_to_analyse)
    OM.printseparator(0)


def print_scc_prolog(config, unk_sccs):
    if not config.get("print_scc_prolog", False):
        return
    if len(unk_sccs) == 0:
        OM.printf("No pending sccs to print as prolog.")
        return
    OM.printseparator(0)
    count = 0
    for scc in unk_sccs:
        scc.toEspecialProlog(config["print_scc_prolog"], count, config["name"])
        count += 1
    OM.printseparator(0)


def compute_reachability(cfg, abstract_domain="polyhedra", do=True, threshold_modes=[], user_props=False, init_nodes=[]):
    if not do:
        return
    cfg.build_polyhedrons()
    node_inv = nodeproperties.compute_reachability(cfg, abstract_domain, threshold_modes=threshold_modes,
                                                   user_props=user_props, init_nodes=init_nodes)
    OM.printseparator(0)
    OM.printf("REACHABILITY ({})".format(abstract_domain))
    OM.printf("\n".join(["-> " + str(n) + " = " +
                         str(node_inv[n])
                         for n in sorted(node_inv)]))
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
        if config.get("termination", None) is not None:
            config["termination"] = [alg for alg in config["termination"] if alg is not None]
        if config.get("nontermination", None) is not None:
            config["nontermination"] = [alg for alg in config["nontermination"] if alg is not None]
        if config["cfr_strategy_scc"] and config["cfr_strategy_after"]:
            raise argparse.ArgumentTypeError("CFR strategies `scc` and `after` can not be applied together.")
        launch(config)
    finally:
        OM.show_output()

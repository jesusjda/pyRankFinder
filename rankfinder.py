import argparse
import invariants
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
    try:
        return TAM.get_algorithm(value)
    except ValueError:
        raise argparse.ArgumentTypeError("{} is not a valid termination algorithm.".format(value))


def termination_alg_desc():
    return ("Algorithms allowed:\n\t"
            + "\n\t".join(TAM.options(True)))


def nontermination_alg(value):
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
    argParser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawTextHelpFormatter)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    argParser.add_argument("-V", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("--dotDestination", required=False,
                           help="Folder to save dot graphs.")
    argParser.add_argument("--tmpdir", required=False, default=None,
                           help="Temporary directory.")
    argParser.add_argument("--prologDestination", required=False,
                           help="Folder to save prolog source.")
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
    argParser.add_argument("--fc-out", required=False, action='store_true',
                           help="Shows the output in fc format")
    # Algorithm Parameters
    argParser.add_argument("-dt", "--different_template", required=False,
                           choices=dt_options, default=dt_options[0],
                           help="Use different templates on each node")
    argParser.add_argument("-sccd", "--scc_depth", type=positive, default=1,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-sc", "--simplify_constraints", required=False,
                           default=False, action='store_true',
                           help="Simplify constraints")
    argParser.add_argument("-lib", "--lib", required=False, choices=["ppl", "z3"],
                           default="ppl", help="select lib")
    # CFR Parameters
    argParser.add_argument("-cfr-st", "--cfr-strategy", required=False, nargs='+',
                           choices=[0,1,2,3,4,"RFS","MANUAL"], default=[4],
                           help="")
    argParser.add_argument("-cfr-it", "--cfr-iteration", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=0)
    argParser.add_argument("-cfr-it-st", "--cfr-iteration-strategy", required=False,
                           choices=["acumulate", "inmutate", "recopute"], default="recompute",
                           help="")
    argParser.add_argument("-cfr-usr", "--cfr-user-properties", default="ignore",
                           choices=["add", "replaceby","ignore","base"],
                           help="")
    
    
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-nt", "--nontermination", type=nontermination_alg,
                           nargs='*', required=False,
                           help=nontermination_alg_desc())
    argParser.add_argument("-t", "--termination", type=termination_alg,
                           nargs='*', required=False,
                           help=termination_alg_desc())
    argParser.add_argument("-i", "--invariants", required=False,
                           default="none", help="Compute Invariants.")
    argParser.add_argument("--threshold", required=False, action='store_true',
                           help="Use user thresholds.")
    argParser.add_argument("-pe", "--pe_modes", type=int, required=False, nargs='+',
                           choices=range(0,5), default=[4],
                           help="List of levels of Partial evaluation in the order that you want to apply them.")
    argParser.add_argument("-pt", "--pe_times", type=int, choices=range(0, 5),
                           help="# times to apply pe", default=1)
    return argParser


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
            OM.printerrf("Parser Error:\n", e)
        return

    config["vars_name"] = cfg.get_info("global_vars")
    OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])

    OM.show_output()
    OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])

    # Compute Termination
    termination_result = None
    nontermination_result = None
    has_to_run = lambda key: key in config and config[key]

    if has_to_run("termination"):
        termination_result = study_termination(config, '/'.join(aux_p[aux_c:]), cfg)
        OM.show_output()
        OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    if has_to_run("nontermination"):
        nontermination_result = study_nontermination(config, cfg, termination_result)
        OM.show_output()
        OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    if termination_result:
        show_termination_result(termination_result, cfg)
        OM.show_output()
        OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    if nontermination_result:
        show_nontermination_result(nontermination_result, cfg)
        OM.show_output()
        OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    
    if "fc_out" in config and config["fc_out"]:
        OM.restart(odest=out, cdest="Fc-Result", vars_name=config["vars_name"])
        from io import StringIO
        fcSource = StringIO()
        cfg.toFc(fcSource)
        OM.printf(fcSource.getvalue())
        fcSource.close()
    return termination_result


def study_termination(config, name, cfg):
    algs = config["termination"]
    tmpdir = None
    if "tmpdir" in config:
        tmpdir = config["tmpdir"]
    if "lib" in config:
        for alg in algs:
            alg.set_prop("lib", config["lib"])
    if config["different_template"] == "always":
        dt_modes = [True]
    elif config["different_template"] == "iffail":
        dt_modes = [False, True]
    else:
        dt_modes = [False]
    skip = False
    for pe_mode in config["pe_modes"]:
        if skip:
            break
        if config["pe_times"] == 0:
            skip = True
        else:
            OM.printif(1, "- Partial Evaluation mode: {}".format(pe_mode))
        print("=="*40)
        pe_cfg = cfg
        pe_cfg.build_polyhedrons()
        compute_invariants(pe_cfg, invariant_type=config["invariants"])
        pe_cfg.simplify_constraints()
        for _ in range(config["pe_times"]):
            if pe_mode == 0:
                break
            pe_cfg.build_polyhedrons()
            pe_cfg = partialevaluate(pe_cfg,  invariant_type=config["invariants"])
            compute_invariants(pe_cfg, invariant_type=config["invariants"])
            pe_cfg.simplify_constraints()
        invariants.use_invariants(pe_cfg, config["invariants"])
        if "dotDestination" in config:
            write_dotfile(config["dotDestination"], name, pe_cfg)
        r = termination.study(algs, pe_cfg, sccd=config["scc_depth"],
                              dt_modes=dt_modes)
        
        if r.get_status().is_terminate():
            return r
    return r


def study_nontermination(config, cfg, termination_result):
    sols = []
    for alg in config["nontermination"]:
        sols += alg.run(cfg)
    return sols

def show_termination_result(result, cfg):
    OM.printseparator(1)
    OM.printf("Final Termination Result")
    no_lin = [tr["name"] for tr in cfg.get_edges() if not tr["linear"]]
    if no_lin:
        OM.printf("Removed no linear constraints from transitions: " +
                  str(no_lin))
    OM.printf(result.toString(cfg.get_info("global_vars")))
    OM.printseparator(1)

def show_nontermination_result(result, cfg):
    OM.printseparator(1)
    OM.printf("Final NON-Termination Result")
    for n, m in result:
        OM.printf("{} : {}".format(n,m))
    OM.show_output()
    OM.printseparator(1)

def write_dotfile(dotDestination, name, cfg):
    if dotDestination:
            s = name.replace('/', '_')
            dot = os.path.join(dotDestination, s + ".dot")
            cfg.toDot(dot)

def write_prologfile(prologDestination, name, cfg):
    if prologDestination:
            s = name.replace('/', '_')
            dot = os.path.join(prologDestination, s + ".pl")
            cfg.toProlog(dot)

def compute_invariants(cfg, invariant_type, use=True, use_threshold=False):
    cfg.build_polyhedrons()
    node_inv = invariants.compute_invariants(cfg, invariant_type, use_threshold=use_threshold)
    if use:
        OM.printseparator(1)
        OM.printif(1, "INVARIANTS ({})".format(invariant_type))
        gvars = cfg.get_info("global_vars")
        OM.printif(1, "\n".join(["-> " + str(n) + " = " +
                                 str(node_inv[n].toString(gvars))
                                 for n in sorted(node_inv)]))
        OM.printseparator(1)
    if use:
        invariants.use_invariants(cfg, invariant_type)
    

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
        # if(not(config["termination"]) and
        #   not(config["nontermination"])):
        #    argParser.error("Either --termination or --nontermination algorithms is required.")
        launch(config)
    finally:
        OM.show_output()

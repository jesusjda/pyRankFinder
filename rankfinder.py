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
    argParser.add_argument("--tmpdir", required=False, default=None,
                           help="Temporary directory.")
    argParser.add_argument("--prologDestination", required=False,
                           help="Folder to save prolog source.")
    argParser.add_argument("-of", "--output-formats", required=False, nargs='+',
                           choices=["fc", "dot", "koat", "pl", "svg"], default=["fc", "dot", "svg"],
                           help="Formats to print the graphs.")
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
    argParser.add_argument("--fc-out", required=False, action='store_true',
                           help="Shows the output in fc format")
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
                           default="ppl", help="select lib")
    # CFR Parameters
    argParser.add_argument("-cfr-au", "--cfr-automatic-properties", required=False, nargs='+',
                           type=int, choices=range(0,5), default=[4],
                           help="")
    argParser.add_argument("-cfr-it", "--cfr-iterations", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=0)
    argParser.add_argument("-cfr-it-st", "--cfr-iteration-strategy", required=False,
                           choices=["acumulate", "inmutate", "recompute"], default="recompute",
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
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-nt", "--nontermination", type=nontermination_alg,
                           nargs='*', required=False,
                           help=nontermination_alg_desc())
    argParser.add_argument("-t", "--termination", type=termination_alg,
                           nargs='*', required=False,
                           help=termination_alg_desc())
    argParser.add_argument("-i", "--invariants", required=False, choices=absdomains,
                           default="none", help="Compute Invariants.")
    argParser.add_argument("-ithre", "--invariants-threshold", required=False,
                           action='store_true', help="Use user thresholds.")
    argParser.add_argument("-caf", "--continue-after-fail", required=False,
                           default=False, action='store_true',
                           help="If an SCC fails it will continue analysing the rest.")
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

def remove_no_important_variables(cfg, doit=False):
    if not doit:
        return
    def are_related_vars(vs, vas):
        if len(vs) != 2: 
            return False
        N = int(len(vas)/2)
        try:
            pos1 = vas.index(vs[0])
            pos2 = vas.index(vs[1])
        except:
            return False
        return pos1%N == pos2%N
        
    gvars = cfg.get_info("global_vars")
    N = int(len(gvars)/2)
    nivars = list(gvars[:N])
    for tr in cfg.get_edges():
        for c in tr["constraints"]:
            if c.isequality():
                if c.get_independent_term() == 0 and are_related_vars(c.get_variables(), gvars):
                    continue
            for v in c.get_variables():
                if v in tr["local_vars"]:
                    continue
                pos = gvars.index(v)
                vt = gvars[pos%N]
                if vt in nivars:
                    nivars.remove(vt)

            if len(nivars) == 0:
                break
        if len(nivars) == 0:
            break
    count = 0
    for v in nivars:
        pos = gvars.index(v)
        vp = gvars[pos+N]
        for tr in cfg.get_edges():
            for c in list(tr["constraints"]):
                vs = c.get_variables()
                if v in vs or vp in vs:
                    count += 1
                    tr["constraints"].remove(c)
        pos = gvars.index(v)
        gvars.pop(pos+N)
        gvars.pop(pos)
        N = int(len(gvars)/2)
    OM.printif(1, "Removed {} constraint(s) with variables: [{}]".format(count, ",".join(nivars)))

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

    OM.show_output()
    OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    if config["user_reachability"]:
        cfg.build_polyhedrons()
        compute_reachability(cfg, abstract_domain="polyhedra", use=config["user_reachability"],
                             use_threshold=config["invariants_threshold"])
        return None
    # Compute Termination
    termination_result = None
    nontermination_result = None
    has_to_run = lambda key: key in config and config[key]
    if has_to_run("termination"):
        termination_result = analyse_termination(config , cfg)
        OM.show_output()
        OM.restart(odest=out, cdest=r, vars_name=config["vars_name"])
    if has_to_run("nontermination"):
        nontermination_result = analyse_nontermination(config, cfg, termination_result)
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
    ncfg = {}
    ncfg["name"] = config["name"]
    ncfg["output_destination"] = config["output_destination"]
    ncfg["output_formats"] = ["fc", "svg"]
    showgraph(cfg, ncfg, sufix="_anotated", console=True, writef=False)
    return termination_result

def showgraph(cfg, config, sufix="", console=False, writef=False):
    if not console and not writef:
        return
    name = config["name"] +str(sufix)
    destname = config["output_destination"]
    if destname is None:
        return

    os.makedirs(os.path.dirname(destname), exist_ok=True)
    invariant_type = config["invariants"] if "invariants" in config else None
    from io import StringIO
    stream = StringIO()
    if "fc" in config["output_formats"]:
        cfg.toFc(stream)
        fcstr=stream.getvalue()
        if console:
            OM.printif(0, "Graph {}".format(name), consoleid="source", consoletitle="Fc Source")
            OM.printif(0, fcstr, format="text", consoleid="source", consoletitle="Fc Source")
        if writef:
            OM.writefile(0, name+".fc", fcstr)
        stream.close()
        stream = StringIO()
    if "dot" in config["output_formats"] or "svg" in config["output_formats"]:
        cfg.toDot(stream)
        dotstr = stream.getvalue()
        dotfile = os.path.join(destname, name+".dot")
        os.makedirs(os.path.dirname(dotfile), exist_ok=True)
        
        with open(dotfile, "w") as f:
            f.write(dotstr)
        stream.close()
        stream = StringIO()
        if "dot" in config["output_formats"] and writef:
            if console:
                OM.printif(0, "Graph {}".format(name), consoleid="graphs", consoletitle="Graphs")
                OM.printif(0, dotstr, format="text", consoleid="graphs", consoletitle="Graphs")
            if writef:
                OM.writefile(0, name+".dot", dotstr)
        if "svg" in config["output_formats"]:
            svgfile = os.path.join(destname, name+".svg")
            svgstr = dottoSvg(dotfile, svgfile)
            if console:
                OM.printif(0, "Graph {}".format(name), consoleid="graphs", consoletitle="Graphs")
                OM.printif(0, svgstr, format="svg", consoleid="graphs", consoletitle="Graphs")
            if writef:
                OM.writefile(0, name+".svg", svgstr)
    if "koat" in config["output_formats"]:
        cfg.toKoat(path=stream, goal_complexity=True, invariant_type=invariant_type)
        koatstr=stream.getvalue()
        OM.printif(0, "Graph {}".format(name), consoleid="koat", consoletitle="koat Source")
        OM.printif(0, koatstr, format="text", consoleid="koat", consoletitle="koat Source")
        OM.writefile(0, name+".koat", koatstr)
        stream.close()
        stream = StringIO()
    stream.close()

def dottoSvg(dotfile, svgfile):
    from subprocess import check_call
    check_call(['dot', '-Tsvg', dotfile ,'-o', svgfile])
    check_call(['sed', '-i','-e', ':a', '-re', '/<!.*?>/d;/<\?.*?>/d;/<!/N;//ba', svgfile])
    svgstr = ""
    with open(svgfile, "r") as f:
        svgstr += f.read()
    return svgstr

def file2string(filepath):
    with open(filepath, 'r') as f:
        data=f.read()
    return data

def control_flow_refinement(cfg, config, au_prop=4, console=False, writef=False):
    cfr_ite = config["cfr_iterations"]
    cfr_inv = config["cfr_invariants"]
    # cfr_it_st = config["cfr_iteration_strategy"]
    cfr_usr_props = config["cfr_user_properties"]
    cfr_simplify = config["cfr_simplify_constraints"]
    cfr_inv_thre = config["cfr_invariants_threshold"]
    tmpdir = config["tmpdir"]
    pe_cfg = cfg
    sufix = ""
    for it in range(0, cfr_ite):
        compute_invariants(pe_cfg, abstract_domain=cfr_inv, use=False, use_threshold=cfr_inv_thre)
        pe_cfg.simplify_constraints(simplify=cfr_simplify)
        showgraph(pe_cfg, config, sufix=sufix, console=console, writef=writef)
        pe_cfg = partialevaluate(pe_cfg, auto_props=au_prop,
                                 user_props=cfr_usr_props, tmpdir=tmpdir,
                                 invariant_type=cfr_inv)
        sufix="_cfr"+str(it+1)
    showgraph(pe_cfg, config, sufix=sufix, console=console, writef=writef)
    return pe_cfg

def analyse_termination(config, cfg):
    algs = config["termination"]
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
    for au_prop in config["cfr_automatic_properties"]:
        if skip:
            break
        if config["cfr_iterations"] == 0:
            skip = True
        else:
            OM.printif(1, "- CFR properties: {}".format(au_prop))
        OM.printseparator(1)
        #cfg.simplify_constraints()
        pe_cfg = control_flow_refinement(cfg, config, au_prop=au_prop)
        compute_invariants(pe_cfg, abstract_domain=config["invariants"],
                           use_threshold=config["invariants_threshold"])
        r = termination.analyse(algs, pe_cfg, sccd=config["scc_depth"],
                                dt_modes=dt_modes, continue_after_fail=config["continue_after_fail"])
        ncfg = {}
        ncfg["name"] = config["name"]
        ncfg["output_destination"] = config["output_destination"]
        ncfg["output_formats"] = ["fc", "svg"]
        sufix="  iterations:{}, auto:{}, usr:{}, inv:{}".format(config["cfr_iterations"], au_prop,config["cfr_user_properties"], config["cfr_invariants"])
        showgraph(pe_cfg, ncfg, sufix=sufix, console=True, writef=False)
        if r.get_status().is_terminate():
            return r
    return r


def analyse_nontermination(config, cfg, termination_result):
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
    unk_sccs = result.get("unknown_sccs")
    if len(unk_sccs) > 0:
        OM.printf("SCCs where we can not proof termination.")
        for scc in unk_sccs:
            ns = scc.get_nodes()
            ts = scc.get_edges()
            OM.printf("SCC:\n+--transitions: {}\n+--nodes: {}\n".format(
                ",".join([t["name"] for t in ts]), ",".join(ns)))

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

def compute_invariants(cfg, abstract_domain, use=True, use_threshold=False):
    cfg.build_polyhedrons()
    node_inv = invariants.compute_invariants(cfg, abstract_domain, use_threshold=use_threshold)
    if use:
        OM.printseparator(1)
        OM.printif(1, "INVARIANTS ({})".format(abstract_domain))
        gvars = cfg.get_info("global_vars")
        OM.printif(1, "\n".join(["-> " + str(n) + " = " +
                                 str(node_inv[n].toString(gvars))
                                 for n in sorted(node_inv)]))
        OM.printseparator(1)
    if use:
        invariants.use_invariants(cfg, abstract_domain)

def compute_reachability(cfg, abstract_domain="polyhedra", use=True, use_threshold=False):
    cfg.build_polyhedrons()
    node_inv = invariants.compute_reachability(cfg, abstract_domain, use_threshold=use_threshold)
    if use:
        OM.printseparator(0)
        OM.printf("REACHABILITY ({})".format(abstract_domain))
        gvars = cfg.get_info("global_vars")
        OM.printf("\n".join(["-> " + str(n) + " = " +
                              str(node_inv[n].toString(gvars))
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
        # if(not(config["termination"]) and
        #   not(config["nontermination"])):
        #    argParser.error("Either --termination or --nontermination algorithms is required.")
        launch(config)
    finally:
        OM.show_output()



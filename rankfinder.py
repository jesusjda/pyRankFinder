import argparse
from genericparser import GenericParser
from genericparser.Cfg import Cfg
from invariants import ConstraintState
from lpi.Lazy_Polyhedron import C_Polyhedron
import os
import sys
from termination import NonTermination_Algorithm_Manager as NTAM
from termination import Output_Manager as OM
from termination import Result
from termination import Termination_Algorithm_Manager as TAM
import termination
import traceback
from termination.algorithm.utils import get_ppl_transition_polyhedron


_version = "0.0.4"
_name = "rankfinder"


def positive(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("Minimum value is 0")
    return ivalue


def termination_alg(value):
    try:
        return TAM.get_algorithm(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError() from e


def termination_alg_desc():
    return ("Algorithms allowed:\n\t"
            + "\n\t".join(TAM.options(True)))


def nontermination_alg(value):
    try:
        return NTAM.get_algorithm(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError() from e


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
    argParser.add_argument("-ver", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("--dotDestination", required=False,
                           help="Folder to save dot graphs.")
    argParser.add_argument("--prologDestination", required=False,
                           help="Folder to save prolog source.")
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
    # Algorithm Parameters
    argParser.add_argument("-dt", "--different_template", required=False,
                           choices=dt_options, default=dt_options[0],
                           help="Use different templates on each node")
    argParser.add_argument("-sccd", "--scc_depth", type=positive, default=0,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-sc", "--simplify_constraints", required=False,
                           default=False, action='store_true',
                           help="Simplify constraints")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-nt", "--nontermination", type=nontermination_alg,
                           nargs='+', required=False,
                           help=nontermination_alg_desc())
    argParser.add_argument("-t", "--termination", type=termination_alg,
                           nargs='+', required=False,
                           help=termination_alg_desc())
    argParser.add_argument("-i", "--invariants", required=False,
                           default="none", help="Compute Invariants.")
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


def launch_file(config, f, out):
    prs = GenericParser()
    aux_p = f.split('/')
    aux_c = len(aux_p) - 1
    while aux_c > 0:
        if aux_p[aux_c] == "examples":
            break
        if aux_p[aux_c] == "User_Projects":
            break
        aux_c -= 1
    r = '/'.join(aux_p[aux_c:])
    o = out
    try:
        cfg = prs.parse(f)
    except Exception as e:
        OM.restart(odest=o, cdest=r, vars_name=[])
        if out is not None:
            tmpfile = os.path.join(os.path.curdir, out)
            with open(tmpfile, "w") as f:
                print(tmpfile)
                f.write(str(traceback.format_exc()))
        else:
            OM.printf(str(traceback.format_exc()))
            OM.show_output()
        raise Exception() from e

    config["vars_name"] = cfg.get_info("global_vars")
    OM.restart(odest=o, cdest=r, vars_name=config["vars_name"])

    # Pre compute
    build_ppl_polyhedrons(cfg)
    compute_invariants(config["invariants"], cfg)
    simplify_constraints(config["simplify_constraints"], cfg)
    write_dotfile(config["dotDestination"], r, cfg)
    write_prologfile(config["prologDestination"], r, cfg)
    
    OM.show_output()
    OM.restart(odest=o, cdest=r, vars_name=config["vars_name"])

    # Compute Termination
    termination_result = None
    nontermination_result = None
    if config["termination"]:
        termination_result = study_termination(config, cfg)
        OM.show_output()
        OM.restart(odest=o, cdest=r, vars_name=config["vars_name"])
    if config["nontermination"]:
        nontermination_result = study_nontermination(config, cfg, termination_result)
        OM.show_output()
        OM.restart(odest=o, cdest=r, vars_name=config["vars_name"])
    if termination_result:
        show_termination_result(termination_result, cfg)
        OM.show_output()
        OM.restart(odest=o, cdest=r, vars_name=config["vars_name"])
    if nontermination_result:
        show_nontermination_result(nontermination_result, cfg)
        OM.show_output()
    return termination_result


def study_termination(config, cfg):
    return rank(config["termination"],
                [(cfg, config["scc_depth"])],
                config["different_template"])


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
    # tr_rfs = result.get("tr_rfs")
    # OM.printif(3, tr_rfs)
    # for tr in tr_rfs:
    #     OM.print_rf_tr(3, cfg, tr, tr_rfs[tr])
    OM.printseparator(1)
    OM.show_output()
    result = result.found()

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
            cfg.toDot(OM, dot)

def write_prologfile(prologDestination, name, cfg):
    if prologDestination:
            s = name.replace('/', '_')
            dot = os.path.join(prologDestination, s + ".pl")
            cfg.toProlog(dot)

def simplify_constraints(simplify, cfg):
    if simplify:
        for e in cfg.get_edges():
            e["polyhedron"].minimized_constraints()


def build_ppl_polyhedrons(cfg):
    edges = cfg.get_edges()
    global_vars = cfg.get_info("global_vars")
    for e in edges:
        tr_poly = get_ppl_transition_polyhedron(e, global_vars)
        # get_z3_transition_polyhedron(e, global_vars)
        cfg.set_edge_info(source=e["source"], target=e["target"], name=e["name"],
                          key="tr_polyhedron", value=tr_poly)


def compute_invariants(invariant_type, cfg):
    graph_nodes = cfg.nodes()
    nodes = {}
    global_vars = cfg.get_info("global_vars")
    Nvars = len(global_vars)/2
    if(invariant_type is None or
       invariant_type == "none"):
        for node in graph_nodes:
            nodes[node] = {
                "state": ConstraintState(Nvars)
            }
    else:
        def apply_tr(s, tr):
            return s.apply_tr(tr, copy=True)

        def lub(s1, s2):
            return s1.lub(s2, copy=True)

        init_node = cfg.get_info("init_node")
        p = ConstraintState(Nvars, bottom=True)

        for node in graph_nodes:
            nodes[node] = {
                "state": p.copy(),
                "access": 0
            }

        nodes[init_node]["state"] = ConstraintState(Nvars)

        queue = [init_node]
        while len(queue) > 0:
            node = queue.pop()
            s = nodes[node]["state"]
            for t in cfg.get_edges(source=node):
                dest_s = nodes[t["target"]]
                s1 = apply_tr(s, t)
                s2 = lub(dest_s["state"], s1)
                if not s2 <= dest_s["state"]:  # lte(s2, dest_s["state"]):
                    dest_s["access"] += 1
                    if dest_s["access"] >= 3:
                        s2.widening(dest_s["state"])
                        dest_s["access"] = 0
                    dest_s["state"] = s2
                    if not(t["target"] in queue):
                        queue.append(t["target"])

    OM.printif(1, "INVARIANTS")
    for n in nodes:
        cfg.nodes[n]["invariant"] = nodes[n]["state"]
        OM.printif(1, "invariant of " + n, " = ",
                   nodes[n]["state"].get_constraints())

    edges = cfg.get_edges()
    Nvars = len(cfg.get_info("global_vars"))

    OM.printif(3, Nvars)
    for e in edges:
        Nlocal_vars = len(e["local_vars"])
        tr_cons = e["tr_polyhedron"].get_constraints()
        inv = nodes[e["source"]]["state"].get_constraints()
        tr_poly = C_Polyhedron(dim=Nvars+Nlocal_vars)
        for c in tr_cons:
            tr_poly.add_constraint(c)
        for c in inv:
            tr_poly.add_constraint(c)
        OM.printif(3, tr_poly.get_dimension())
        cfg.set_edge_info(source=e["source"], target=e["target"], name=e["name"],
                          key="polyhedron", value=tr_poly)
    OM.printif(3, cfg.get_edges())


def rank(algs, CFGs, different_template="never"):
    if different_template == "always":
        dt = True
    else:
        dt = False
    response = Result()
    rfs = {}
    tr_rfs = {}
    fail = False
    while (not fail and CFGs):
        current_cfg, sccd = CFGs.pop(0)
        if sccd > 0:
            CFGs_aux = current_cfg.get_scc()
        else:
            CFGs_aux = [current_cfg]
        CFGs_aux.sort()
        for cfg in CFGs_aux:
            if not cfg.has_cycle():
                continue
            trs_poly = [t["polyhedron"] for t in cfg.get_edges()]
            skip = False
            for tr_p in trs_poly:
                if tr_p.is_empty():
                    OM.printif(2, "Skipped because one transition is False.")
                    skip = True
                    break
            if skip:
                continue

            R = run_algs(algs, cfg, different_template=dt)
            if not R.found():
                if different_template == "iffail":
                    OM.printif(1, "Using Different Template")
                    R = run_algs(algs, cfg, different_template=True)
            if not R.found():
                fail = True
                break
            merge_rfs(rfs, R.get("rfs"))
            merge_rfs(tr_rfs, R.get("tr_rfs"))
            pending_trs = R.get("pending_trs")
            if pending_trs:
                CFGs = [(cfg.edge_data_subgraph(pending_trs),
                         sccd)] + CFGs
    if fail:
        response.set_response(found=False)
    else:
        response.set_response(found=True)
    response.set_response(rfs=rfs,
                          tr_rfs=tr_rfs,
                          pending_cfgs=CFGs)
    return response


def run_algs(algs, cfg, different_template=False):
    response = Result()
    vars_name = cfg.get_info("global_vars")
    R = None
    f = False
    trans = cfg.get_edges()
    trs = ', '.join(sorted([t["name"] for t in trans]))
    OM.printif(1, "Analyzing transitions: "+trs)
    for alg in algs:
        OM.printif(1, "-> with: " + str(alg))

        R = alg.run(cfg,
                    different_template=different_template)

        OM.printif(3, R.debug())
        OM.printif(1, R.toString(vars_name))
        if R.found():
            if R.get("rfs"):
                f = True
                break

    if f:
        response.set_response(found=True,
                              info="Found",
                              rfs=R.get("rfs"),
                              tr_rfs=R.get("tr_rfs"),
                              pending_trs=R.get("pending_trs"))
        return response
    
    response.set_response(found=False,
                          info="Not Found")
    return response


def merge_rfs(rfs, to_add):
    new_rfs = rfs
    for key in to_add:
        if key in new_rfs:
            if not isinstance(new_rfs[key], list):
                new_rfs[key] = [new_rfs[key]]
            new_rfs[key].append(to_add[key])
        else:
            new_rfs[key] = [to_add[key]]
    return new_rfs


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

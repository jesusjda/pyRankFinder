import argparse
from copy import deepcopy
from genericparser import GenericParser
from genericparser.Cfg import Cfg
import lpi
import os
from ppl import Linear_Expression
from ppl import Variable
from ppl import Variables_Set
import sys
import termination
from termination.output import Output_Manager as OM
import traceback


# import getopt
_version = "0.0.2"
_name = "rankfinder"


def positive(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("Minimum value is 0")
    return ivalue


def algorithm(value):
    algs = ["qlrf_bg", "qlrf_adfg", "lrf_pr"]
    if value in algs:
        return {"name": value}

    if value == "qnlrf":
        return {"name": value,
                "max_depth": 5,
                "min_depth": 1
                }
    import re
    algth = {}
    alg = re.match((r"(?P<name>[a-zA-Z0-9]+)\_"
                    "(?P<arg>(?P<args>[a-zA-Z0-9]+(\_)?)+)"),
                   value)
    if alg is None:
        raise argparse.ArgumentTypeError("Unknown algorithm (" + value + ")")
    fn_dict = alg.groupdict()
    del fn_dict['args']
    fn_dict['arg'] = [arg.strip() for arg in fn_dict['arg'].split('_')]
    if fn_dict['name'] == "qnlrf":
        algth['name'] = "qnlrf"
        if len(fn_dict['arg']) > 0:
            algth['max_depth'] = int(fn_dict['arg'][0])
        if len(fn_dict['arg']) > 1:
            algth['min_depth'] = int(fn_dict['arg'][1])
        else:
            algth['min_depth'] = 1
        if len(fn_dict['arg']) > 2:
            raise argparse.ArgumentTypeError("qnlrf allows 2 " +
                                             "arguments at most (given " +
                                             str(len(fn_dict['arg'])) + ")")
        return algth

    raise argparse.ArgumentTypeError("Unknown algorithm (" + value + ")")


def setArgumentParser():
    desc = _name+": a Ranking Function finder on python."
    dt_options = ["never", "iffail", "always"]
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
    argParser.add_argument("-dt", "--different_template", required=False,
                           choices=dt_options, default=dt_options[0],
                           help="Use different templates on each node")
    argParser.add_argument("-sccd", "--scc_depth", type=positive, default=0,
                           help="Strategy based on SCC to go through the CFG.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-a", "--algorithms", type=algorithm, nargs='+',
                           required=True, help="Algorithms to be apply.")
    argParser.add_argument("-i", "--invariants", required=False,
                           default="none", help="Compute Invariants.")
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

        try:
            if args.dotDestination:
                s = r.replace('/', '_')
                dot = os.path.join(args.dotDestination, s + ".dot")
                cfg = prs.parse(f, dotgraph=dot)
            else:
                cfg = prs.parse(f)
        except Exception as e:
            raise e
        config["vars_name"] = cfg.get_var_name()
        OM.restart(dest=r, vars_name=config["vars_name"])
        invariants(config["invariants"], cfg)

        if config["different_template"] == "always":
            different_template = True
        else:
            different_template = False

        result = rank(config["algorithms"],
                      [(cfg, config["scc_depth"])],
                      different_template)
        if not result.found() and config["different_template"] == "iffail":
            OM.printf(1, "Running algorithms with different template")
            different_template = True
            result = rank(config["algorithms"],
                          [(cfg, config["scc_depth"])],
                          different_template)
        if(len(files) > 1):
            OM.printf(f)
        OM.printseparator(1)
        OM.printf("Final Result")
        if different_template:
            OM.printf("Using Different Template")
        OM.printf(result.toString(cfg.get_var_name()))
        tr_rfs = result.get("tr_rfs")
        OM.printif(3, tr_rfs)
        for tr in tr_rfs:
            OM.print_rf_tr(3, cfg, tr, tr_rfs[tr])
        OM.printseparator(1)
        OM.show_output()
    return


def invariants(invariant_type, cfg):
    # Temporal defs to be compilable
    graph_nodes = cfg.nodes()
    nodes = {}
    Nvars = len(cfg.get_var_name())/2
    OM.printif(2, "invariant type = ", invariant_type)
    if(invariant_type is None or
       invariant_type == "none"):
        for node in graph_nodes:
            nodes[node] = {
                "state": lpi.C_Polyhedron(dim=Nvars)
            }
    else:
        def apply_tr(s, tr):
            poly_tr = tr["tr_polyhedron"]
            m = poly_tr.get_dimension()
            n = s.get_dimension()
            s1 = deepcopy(s)
            s1.add_dimensions(m - n)
            s1.intersection_assign(poly_tr)
            var_set = Variables_Set()
            for i in range(0, n):  # Vars from 0 to n-1 inclusive
                var_set.insert(Variable(i))
            # (local variables)
            for i in range(2*n, m):  # Vars from 2*n to m-1 inclusive
                var_set.insert(Variable(i))

            s1.remove_dimensions(var_set)
            return s1

        def lub(s1, s2):
            a = deepcopy(s1)
            a.poly_hull_assign(s2)
            return a

        init_node = cfg.get_init_node()
        p = lpi.C_Polyhedron(dim=Nvars)
        p.add_constraint(Linear_Expression(0) == Linear_Expression(1))

        for node in graph_nodes:
            nodes[node] = {
                "state": deepcopy(p),
                "access": 0
            }

        nodes[init_node]["state"] = lpi.C_Polyhedron(dim=Nvars)

        queue = [init_node]
        while len(queue) > 0:
            node = queue.pop()
            s = nodes[node]["state"]
            for t in cfg.get_edges(src=node):
                dest_s = nodes[t["target"]]
                s1 = apply_tr(s, t)
                s2 = lub(dest_s["state"], s1)
                if not s2 <= dest_s["state"]:  # lte(s2, dest_s["state"]):
                    dest_s["access"] += 1
                    if dest_s["access"] >= 3:
                        s2.widening_assign(dest_s["state"])
                        dest_s["access"] = 0
                    dest_s["state"] = s2
                    if not(t["target"] in queue):
                        queue.append(t["target"])

    OM.printif(1, "INVARIANTS")
    for n in nodes:
        cfg.add_node_info(n, "invariant", nodes[n]["state"])
        OM.printif(1, "invariant of " + n, " = ",
                   nodes[n]["state"].get_constraints())


def rank(algs, CFGs, different_template=False):
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
            if not cfg.has_cycle():
                continue
            R = run_algs(algs, cfg,
                         different_template=different_template)
            if not R.found():
                fail = True
                break
            merge_rfs(rfs, R.get("rfs"))
            merge_rfs(tr_rfs, R.get("tr_rfs"))
            pending_trs = R.get("pending_trs")
            if pending_trs:
                CFGs = [(Cfg(pending_trs, cfg.get_var_name(),
                             nodes_info=cfg.get_node_info(),
                             init_node=cfg.get_init_node()),
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
    response = termination.Result()
    vars_name = cfg.get_var_name()
    R = None
    f = False
    trans = cfg.get_edges()
    trs = ""
    for t in trans:
        trs += t["name"]+","
    OM.printif(1, "Analyzing transitions: "+trs)
    for alg in algs:
        OM.printif(1, "-> with: " + alg['name'])
        R = termination.run(alg, cfg,
                            different_template=different_template)
        OM.printif(3, R.debug())
        OM.printif(1, R.toString(vars_name))
        if R.found():
            if R.get("rfs"):
                f = True
                break

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

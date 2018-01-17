import argparse
from genericparser import GenericParser
from genericparser.Cfg import Cfg
from invariants import ConstraintState
import os
import sys
import termination
from termination.output import Output_Manager as OM
import traceback
from lpi.Lazy_Polyhedron import C_Polyhedron


_version = "0.0.4"
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
    ver = 1
    if value == "qnlrfv2":
        ver = 2
    if value in ["qnlrf", "qnlrfv2"]:
        return {"name": "qnlrf",
                "max_depth": 5,
                "min_depth": 1,
                "version": ver
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
    if fn_dict['name'] in ["qnlrf", "qnlrfv2"]:
        if fn_dict['name'] == "qnlrfv2":
            ver = 2
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
        algth['version'] = ver
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
    argParser.add_argument("-sc", "--simplify_constraints", required=False,
                           action='store_true', help="Simplify constraints")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-a", "--algorithms", type=algorithm, nargs='+',
                           required=True, help="Algorithms to be apply.")
    argParser.add_argument("-i", "--invariants", required=False,
                           default="none", help="Compute Invariants.")
    return argParser


def launch(config):
    files = config["files"]
    print(files)
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
    try:
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
        cfg = prs.parse(f)
        config["vars_name"] = cfg.get_var_name()
        OM.restart(odest=o, cdest=r, vars_name=config["vars_name"])

        # Pre algorithm
        compute_invariants(config["invariants"], cfg)
        simplify_constraints(config["simplify_constraints"], cfg)
        write_dotfile(config["dotDestination"], r, cfg)


        result = rank(config["algorithms"],
                      [(cfg, config["scc_depth"])],
                      config["different_template"])
        OM.printseparator(1)
        OM.printf("Final Result")
        no_lin = [tr["name"] for tr in cfg.get_edges() if not tr["linear"]]
        if no_lin:
            OM.printf("Removed no linear constraints from transitions: " +
                      str(no_lin))
        OM.printf(result.toString(cfg.get_var_name()))
        tr_rfs = result.get("tr_rfs")
        OM.printif(3, tr_rfs)
        for tr in tr_rfs:
            OM.print_rf_tr(3, cfg, tr, tr_rfs[tr])
        OM.printseparator(1)
        OM.show_output()
        result = result.found()
    except Exception as _:
        result = False
        if out is not None:
            tmpfile = os.path.join(os.path.curdir, out)
            with open(tmpfile, "w") as f:
                print(tmpfile)
                f.write(str(traceback.format_exc()))
        else:
            OM.printf(str(traceback.format_exc()))
            OM.show_output()
    finally:
        pass
    return result


def write_dotfile(dotDestination, name, cfg):
    if dotDestination:
            s = name.replace('/', '_')
            dot = os.path.join(dotDestination, s + ".dot")
            cfg.toDot(OM, dot)


def simplify_constraints(simplify, cfg):
    if simplify:
        for e in cfg.get_edges():
            e["polyhedron"].minimized_constraints()


def compute_invariants(invariant_type, cfg):
    graph_nodes = cfg.nodes()
    nodes = {}
    Nvars = len(cfg.get_var_name())/2
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

        init_node = cfg.get_init_node()
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
            for t in cfg.get_edges(src=node):
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
        cfg.add_node_info(n, "invariant", nodes[n]["state"])
        OM.printif(1, "invariant of " + n, " = ",
                   nodes[n]["state"].get_constraints())

    edges = cfg.get_edges()
    Nvars = len(cfg.get_var_name())

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
        cfg.add_edge_info(src=e["source"], trg=e["target"], name=e["name"],
                          key="polyhedron", value=tr_poly)
    OM.printif(3, cfg.get_edges())


def rank(algs, CFGs, different_template="never"):
    if different_template == "always":
        dt = True
    else:
        dt = False
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
    trs = ', '.join(sorted([t["name"] for t in trans]))
    OM.printif(1, "Analyzing transitions: "+trs)
    for alg in algs:
        
        cad_alg = "-> with: " + alg['name']
        if "version" in alg:
            cad_alg +=  " version: " + str(alg["version"])
        OM.printif(1, cad_alg)

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
            new_rfs[key] = [to_add[key]]
    return new_rfs


if __name__ == "__main__":
    argv = sys.argv[1:]
    argParser = setArgumentParser()
    args = argParser.parse_args(argv)
    OM.verbosity = args.verbosity
    OM.ei = args.ei_out
    if args.version:
        print(_name + " version: " + _version)
        exit(0)
    config = vars(args)
    try:
        launch(config)
    except Exception as e:
        OM.show_output()
        e.traceback()
        exit(-1)

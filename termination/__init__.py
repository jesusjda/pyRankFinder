from .algorithm import NonTermination_Algorithm_Manager
from .algorithm import Termination_Algorithm_Manager
from .output import Output_Manager
from .result import Result
from .result import TerminationResult

__all__ = ["NonTermination_Algorithm_Manager", "Termination_Algorithm_Manager","Output_Manager", "Result", "TerminationResult", "analyse", "analyse_nontermination"]


def analyse(algs, cfg, sccd=1, dt_modes=[False], stop_if_fail=False):
    response = rank(algs,[(cfg,sccd)],dt_modes=dt_modes, stop_if_fail=stop_if_fail)
    response.set_response(cfg_analysed=cfg)
    return response

def analyse_nontermination(algs, scc, close_walk_depth=5, stop_if_fail=False):
    response = None
    for cw in scc.get_close_walks(close_walk_depth):
        Output_Manager.printif(1, "\n\tAnalysing Close Walk: {}.".format([t["name"] for t in cw]))
        for a in algs:
            response = a.run(scc, cw)
            if response.get_status().is_nonterminate():
                break
        if response.get_status().is_nonterminate():
            break
    return response

def rank(algs, CFGs, dt_modes=[False], stop_if_fail=False):
    from .algorithm.utils import merge
    response = Result()
    rfs = {}
    fail = False
    unknown_sccs = []
    while (not fail and CFGs):
        current_cfg, sccd = CFGs.pop(0)
        if len(current_cfg.get_edges()) == 0:
            Output_Manager.printif(2, "CFG ranked because it is empty.")
            continue
        for t in current_cfg.get_edges():
            if t["polyhedron"].is_empty():
                Output_Manager.printif(2, "Transition ("+t["name"]+") removed because it is empty.")
                current_cfg.remove_edge(t["source"], t["target"], t["name"])
        if sccd > 0:
            CFGs_aux = current_cfg.get_scc()
        else:
            CFGs_aux = [current_cfg]
        CFGs_aux.sort()
        for cfg in CFGs_aux:
            R = analyse_scc(algs, cfg, dt_modes=dt_modes)
            if R is None:
                continue
            if not R:
                fail = True
                unknown_sccs.append(cfg)
                if stop_if_fail:
                    break
                continue
            merge(rfs, R.get("rfs"))
            pending_trs = R.get("pending_trs")
            if pending_trs:
                CFGs = [(cfg.edge_data_subgraph(pending_trs),
                         sccd)] + CFGs
    if fail:
        response.set_response(status=TerminationResult.UNKNOWN)
    else:
        response.set_response(status=TerminationResult.TERMINATE)
    response.set_response(rfs=rfs,
                          pending_cfgs=CFGs,
                          unknown_sccs=unknown_sccs)
    return response


def analyse_scc(algs, cfg, dt_modes=[False]):
    trans = cfg.get_edges()
    nodes = ', '.join(sorted(cfg.get_nodes()))
    trs = ', '.join(sorted([t["name"] for t in trans]))
    Output_Manager.printif(1, "SCC\n+-- Transitions: {}\n+-- Nodes: {}".format(trs, nodes))
    if not trans:
        Output_Manager.printif(1, "-> Ranked because it has not transitions.")
        return None
    if not cfg.has_cycle():
        Output_Manager.printif(1, "-> Ranked because it has not cycles.")
        return None
    found = False

    for dt in dt_modes:
        if dt:
            Output_Manager.printif(1, "\t- Using Different Template") 
        R = run_algs(algs, cfg, different_template=dt)
        if R.has("info"):
            Output_Manager.printif(1, R.get("info"))
        if R.get_status().is_terminate():
            Output_Manager.printif(2, "--> Found with dt={}.\n".format(dt))
            vars_name = cfg.get_info("global_vars")
            Output_Manager.printif(1, R.toStrRankingFunctions(vars_name))
            found = True
            break
    if found:
        return R
    else:
        return False


def run_algs(algs, cfg, different_template=False):
    response = Result()
    R = None
    f = False
    if len(cfg.get_edges()) == 0:
        response.set_response(status=TerminationResult.TERMINATE,
                              info="Empty Cfg",
                              rfs=[],
                              pending_trs=[])
        return response
    for alg in algs:
        Output_Manager.printif(1, "\t-> with: " + str(alg))

        R = alg.run(cfg,
                    different_template=different_template)

        Output_Manager.printif(3, R.debug())
        if R.get_status().is_terminate():
            if R.get("rfs"):
                f = True
                break
    if f:
        response.set_response(status=TerminationResult.TERMINATE,
                              info="Found",
                              rfs=R.get("rfs"),
                              pending_trs=R.get("pending_trs"))
        return response
    
    response.set_response(status=TerminationResult.UNKNOWN,
                          info="Not Found")
    return response

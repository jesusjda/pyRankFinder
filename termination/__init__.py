from .algorithm import NonTermination_Algorithm_Manager
from .algorithm import Termination_Algorithm_Manager
from .output import Output_Manager
from .result import Result
from .result import TerminationResult

__all__ = ["NonTermination_Algorithm_Manager", "Termination_Algorithm_Manager", "Output_Manager", "Result", "TerminationResult", "analyse"]

def analyse(config, cfg):
    fast_answer_result = Result()
    fast_answer_result.set_response(status=TerminationResult.UNKNOWN)
    # configuration
    t_algs = config["termination"] if "termination" in config else []
    nt_algs = config["nontermination"] if "nontermination" in config else []
    if len(t_algs) == 0 and len(nt_algs) == 0:
        fast_answer_result.set_response(info="No algorithms selected", graph=cfg)
        return fast_answer_result
    if "lib" in config:
        for alg in t_algs:
            alg.set_prop("lib", config["lib"])
        for alg in nt_algs:
            alg.set_prop("lib", config["lib"])
    if config["different_template"] == "always":
        dt_modes = [True]
    elif config["different_template"] == "iffail":
        dt_modes = [False, True]
    else:
        dt_modes = [False]
    cfr = {"cfr_iterations":0}
    if "cfr_strategy" in config:
        cfr_scc = config["cfr_strategy"] in ["scc"]
        if cfr_scc:
            cfr ={"cfr_automatic_properties": config["cfr_automatic_properties"],
                  "cfr_user_properties": config["cfr_user_properties"],
                  "cfr_iterations": config["cfr_iterations"],
                  "cfr_invariants": config["cfr_invariants"],
                  "cfr_invariants_threshold": config["cfr_invariants_threshold"],
                  "tmpdir": config["tmpdir"]
                  }
            if not cfr["cfr_user_properties"] and cfr["cfr_automatic_properties"] == 0:
                cfr["cfr_iterations"] = 0
    max_sccd = config["scc_depth"]
    fast_answer = config["stop_if_fail"]
    # SCC spliting and analysis
    from .algorithm.utils import merge
    stop = False
    CFGs = [(cfg, max_sccd, False)]
    rfs = {}
    while (not stop and CFGs):
        current_cfg, sccd, cfred = CFGs.pop(0)
        for t in current_cfg.get_edges():
            if t["polyhedron"].is_empty():
                Output_Manager.printif(2, "Transition ("+t["name"]+") removed because it is empty.")
                current_cfg.remove_edge(t["source"], t["target"], t["name"])
        if len(current_cfg.get_edges()) == 0:
            Output_Manager.printif(2, "This cfg has not transitions.")
            continue

        CFGs_aux = current_cfg.get_scc() if sccd > 0 else [current_cfg]
        sccd -= 1
        CFGs_aux.sort()
        maybe_sccs = []
        terminating_sccs = []
        nonterminating_sccs = []

        can_be_terminate = len(t_algs) > 0
        can_be_nonterminate = len(nt_algs) > 0
        do_cfr = cfr["cfr_iterations"] > 0 and not cfred
        for scc in CFGs_aux:
            for t in scc.get_edges():
                if t["polyhedron"].is_empty():
                    #OM.printif(2, "Transition ("+t["name"]+") removed because it is empty.")
                    scc.remove_edge(t["source"], t["target"], t["name"])
                    continue
            if len(scc.get_edges()) == 0:
                #OM.printif(2, "CFG ranked because it is empty.")
                continue
            R = False
            R_nt = False
            # analyse termination
            if can_be_terminate:
                R = analyse_scc_termination(t_algs, scc, dt_modes=dt_modes)
            if not R or not R.get_status().is_terminate():
                # analyse NON-termination
                if can_be_nonterminate:
                    R_nt = analyse_scc_nontermination(nt_algs, scc)
                    if R_nt and R_nt.get_status().is_nonterminate():
                        R_nt.set_response(graph=scc)
                        nonterminating_sccs.append(R_nt)
                        if fast_answer:
                            return R_nt
                        continue
                can_be_terminate = not fast_answer or (do_cfr and can_be_terminate)
                if fast_answer and not can_be_terminate and not can_be_nonterminate:
                    fast_answer_result.set_response(info="NON-termination is not being analysed and terminate can't be proved.",
                                                    graph=scc)
                    return fast_answer_result
                if not do_cfr:
                    maybe_sccs.append(scc)
            else:
                merge(rfs, R.get("rfs"))
                pending_trs = R.get("pending_trs")
                R.set_response(graph=scc)
                terminating_sccs.append(R)
                if pending_trs:
                    CFGs = [(cfg.edge_data_subgraph(pending_trs),
                             sccd, False)] + CFGs
                continue
            # try with cfr
            if do_cfr:
                cfg_cfr = None
                from partialevaluation import control_flow_refinement
                from partialevaluation import prepare_scc
                cfg_cfr = control_flow_refinement(prepare_scc(cfg,scc,"polyhedra"), cfr)
                cfr_CFGs_aux = cfg_cfr.get_scc() if sccd > 0 else [cfg_cfr]
                sccd -= 1
                cfr_CFGs_aux.sort()
                for cfr_scc in cfr_CFGs_aux:
                    for t in cfr_scc.get_edges():
                        if t["polyhedron"].is_empty():
                            #OM.printif(2, "Transition ("+t["name"]+") removed because it is empty.")
                            cfr_scc.remove_edge(t["source"], t["target"], t["name"])
                            continue
                        if len(cfr_scc.get_edges()) == 0:
                            #OM.printif(2, "CFG ranked because it is empty.")
                            continue
                    R = False
                    R_nt = False
                    # analyse termination with cfr
                    if can_be_terminate:
                        R = analyse_scc_termination(t_algs, cfr_scc, dt_modes=dt_modes)
                    if not R or not R.get_status().is_terminate():
                        # analyse NON-termination with cfr
                        if can_be_nonterminate:
                            R_nt = analyse_scc_nontermination(nt_algs, cfr_scc)
                            if R_nt and R_nt.get_status().is_nonterminate():
                                R_nt.set_response(graph=cfr_scc)
                                nonterminating_sccs.append(R_nt)
                                if fast_answer:
                                    return R_nt
                                continue
                        can_be_terminate = not fast_answer
                        if fast_answer and not can_be_nonterminate:
                            fast_answer_result.set_response(info="NON-termination is not being analysed and terminate can't be proved.",
                                                            graph=cfr_scc)
                            return fast_answer_result
                        maybe_sccs.append(cfr_scc)
                    else:
                        merge(rfs, R.get("rfs"))
                        pending_trs = R.get("pending_trs")
                        R.set_response(graph=cfr_scc)
                        terminating_sccs.append(R)
                        if pending_trs:
                            CFGs = [(cfg.edge_data_subgraph(pending_trs),
                                     sccd, True)] + CFGs
                        continue

    status=TerminationResult.UNKNOWN
    if len(nonterminating_sccs) > 0:
        status=TerminationResult.NONTERMINATE
    elif len(maybe_sccs) > 0:
        status=TerminationResult.UNKNOWN
    else:
        status=TerminationResult.TERMINATE
    response = Result()
    response.set_response(status=status,
                          rfs=rfs,
                          terminate=terminating_sccs,
                          nonterminate=nonterminating_sccs,
                          unknown_sccs=maybe_sccs,
                          graph=cfg)
    return response

def analyse_scc_nontermination(algs, scc, close_walk_depth=5):
    for cw in scc.get_close_walks(close_walk_depth):
        Output_Manager.printif(1, "\nAnalysing Close Walk: {}.".format([t["name"] for t in cw]))
        for a in algs:
            response = a.run(scc, cw)
            if response.get_status().is_nonterminate():
                return response
    return False

def analyse_scc_termination(algs, cfg, dt_modes=[False]):
    trans = cfg.get_edges()
    nodes = ', '.join(sorted(cfg.get_nodes()))
    trs = ', '.join(sorted([t["name"] for t in trans]))
    answer = Result()
    Output_Manager.printif(1, "SCC\n+-- Transitions: {}\n+-- Nodes: {}".format(trs, nodes))
    if not trans:
        answer.set_response(status=TerminationResult.TERMINATE,
                            info="No transitions")
        Output_Manager.printif(1, "-> Ranked because it has not transitions.")
        return answer
    if not cfg.has_cycle():
        answer.set_response(status=TerminationResult.TERMINATE,
                            info="No cycles.")

        Output_Manager.printif(1, "-> Ranked because it has not cycles.")
        return answer

    for dt in dt_modes:
        if dt:
            Output_Manager.printif(1, "- Using Different Template") 
        R = run_algs(algs, cfg, different_template=dt)
        if R.has("info"):
            Output_Manager.printif(1, R.get("info"))
        if R.get_status().is_terminate():
            Output_Manager.printif(2, "--> Found with dt={}.\n".format(dt))
            Output_Manager.printif(1, R.toStrRankingFunctions(cfg.get_info("global_vars")))
            return R
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
        Output_Manager.printif(1, "--> with: " + str(alg))

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

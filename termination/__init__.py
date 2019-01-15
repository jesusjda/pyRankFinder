from .algorithm import NonTermination_Algorithm_Manager
from .algorithm import Termination_Algorithm_Manager
from .output import Output_Manager
from .result import Result
from .result import TerminationResult
from .algorithm.utils import showgraph
from nodeproperties import compute_invariants

__all__ = ["NonTermination_Algorithm_Manager", "Termination_Algorithm_Manager", "Output_Manager", "Result", "TerminationResult", "analyse"]

# alias
OM = Output_Manager

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
    cfr = {"cfr_iterations":0, "cfr_max_tries":0}
    cfr_scc = config["cfr_strategy_scc"]
    cfr_after = config["cfr_strategy_after"]
    cfr_before = config["cfr_strategy_before"]
    if cfr_scc or cfr_after or cfr_before:
        cfr = {"cfr_iterations": config["cfr_iterations"],
               "cfr_invariants": config["cfr_invariants"],
               "cfr_invariants_threshold": config["cfr_invariants_threshold"],
               "cfr_max_tries": config["cfr_max_tries"],
               "tmpdir": config["tmpdir"]
              }
        from nodeproperties.cfrprops import cfrprops_options
        do_it = False
        for op in cfrprops_options():
            cfr[op] = config[op] if op in config else False
            do_it = do_it or cfr[op]
        if not do_it:
            cfr["cfr_iterations"] = 0
            cfr["cfr_max_tries"] = 0
            cfr_scc = False
            cfr_after = False
            cfr_before = False
    max_sccd = config["scc_depth"]
    fast_answer = config["stop_if_fail"]
    rmded = cfg.remove_unsat_edges()
    if len(rmded)> 0:
        OM.printif(1, "Removed edges {} because they where unsat.".format(rmded))
    showgraph(cfg, config, sufix="", console=config["print_graphs"], writef=False, output_formats=["fc", "svg"])
    from .algorithm.utils import merge
    rfs = {}
    maybe_sccs = []
    terminating_sccs = []
    nonterminating_sccs = []
    stop_all = False
    original_cfg = cfg
    # cfr loop
    cfr_it = -1
    from partialevaluation import control_flow_refinement
    from partialevaluation import prepare_scc
    from .algorithm.utils import compute_way_nodes
    from nodeproperties.assertions import check_assertions
    compute_invariants(cfg, abstract_domain=config["invariants"],
                       use_threshold=config["invariants_threshold"],
                       check=config["check_assertions"],
                       add_to_polyhedron=True)
    while (not stop_all and cfr_it < cfr["cfr_max_tries"]):
        cfr_it += 1
        if cfr_before and cfr_it == 0:
            cfg = control_flow_refinement(cfg, cfr)
            compute_invariants(cfg, abstract_domain=config["invariants"],
                               use_threshold=config["invariants_threshold"],
                               check=config["check_assertions"],
                               add_to_polyhedron=True)
            showgraph(cfg, config, sufix="cfr_before", console=config["print_graphs"], writef=False, output_formats=["fc", "svg"])
            CFGs = [(cfg, max_sccd, 0)]
        elif cfr_after and cfr_it != 0:
            if len(maybe_sccs) == 0:
                stop_all = True
                continue
            important_nodes = [n for scc in maybe_sccs for n in scc.get_nodes()]
            maybe_sccs = []
            OM.printif(2, "Nodes to refine")
            OM.printif(2, str(important_nodes))
            way_nodes = compute_way_nodes(cfg, important_nodes)
            OM.printif(3, "Nodes on the way")
            OM.printif(3, str(way_nodes))
            cfg.remove_nodes_from([n for n in cfg.get_nodes() if n not in way_nodes])
            cfg = control_flow_refinement(cfg, cfr, only_nodes=important_nodes)
            new_important_nodes = [n for n in cfg.get_nodes() for n1 in important_nodes if "n_"+n1 == n[:len(n1)+2]]
            compute_invariants(cfg, abstract_domain=config["invariants"],
                              use_threshold=config["invariants_threshold"],
                              add_to_polyhedron=True)
            OM.printif(3, "Important nodes from the cfr graph.")
            OM.printif(3, str(new_important_nodes))
            cfg.remove_nodes_from([n for n in cfg.get_nodes() if n not in new_important_nodes])
            showgraph(cfg, config, sufix="cfr_after_"+str(cfr_it), console=config["print_graphs"], writef=False, output_formats=["fc", "svg"])
            CFGs = [(scc, max_sccd, 0) for scc in cfg.get_scc() if len(scc.get_edges()) > 0]
        else:
            CFGs = [(cfg, max_sccd, 0)]
        stop = False
        # SCC spliting and analysis
        while (not stop and CFGs):
            current_cfg, sccd, cfr_num = CFGs.pop(0)
            for t in current_cfg.get_edges():
                if t["polyhedron"].is_empty():
                    OM.printif(2, "Transition ("+t["name"]+") removed because it is empty.")
                    current_cfg.remove_edge(t["source"], t["target"], t["name"])
            if len(current_cfg.get_edges()) == 0:
                OM.printif(2, "This cfg has not transitions.")
                OM.printif(2, "|-- nodes: {}".format(cfg.get_nodes()))
                continue
            cfg_cfr = current_cfg
            if cfr_scc and cfr_num > 0:
                cfg_cfr = control_flow_refinement(prepare_scc(cfg, current_cfg, "polyhedra"), cfr, inner_invariants=False)
            CFGs_aux = cfg_cfr.get_scc() if sccd > 0 else [cfg_cfr]
            sccd -= 1
            CFGs_aux.sort()

            can_be_terminate = len(t_algs) > 0
            can_be_nonterminate = len(nt_algs) > 0
            do_cfr_scc = cfr_scc and cfr_num < cfr["cfr_max_tries"]
            for scc in CFGs_aux:
                for t in scc.get_edges():
                    if t["polyhedron"].is_empty():
                        scc.remove_edge(t["source"], t["target"], t["name"])
                        continue
                if len(scc.get_edges()) == 0:
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
                                stop = True
                                stop_all = True
                                break
                            continue
                    can_be_terminate = not fast_answer or (do_cfr_scc and can_be_terminate)
                    if fast_answer and not can_be_terminate and not can_be_nonterminate:
                        stop = True
                        break
                    if do_cfr_scc:
                        CFGs = [(scc, max_sccd, cfr_num + 1)] + CFGs
                    else:
                        maybe_sccs.append(scc)
                else:
                    if R.has("rfs"):
                        merge(rfs, R.get("rfs"))
                    pending_trs = R.get("pending_trs") if R.has("pending_trs") else []
                    R.set_response(graph=scc)
                    terminating_sccs.append(R)
                    if pending_trs:
                        CFGs = [(cfg.edge_data_subgraph(pending_trs),
                                 sccd, cfr_num)] + CFGs
                    continue
        if len(maybe_sccs) == 0 or not cfr_after:
            stop_all = True

    status=TerminationResult.UNKNOWN
    if len(nonterminating_sccs) > 0:
        status=TerminationResult.NONTERMINATE
    elif len(maybe_sccs) > 0:
        status=TerminationResult.UNKNOWN
    else:
        status=TerminationResult.TERMINATE
    response = Result()
    response.set_response(status=status,
                          rfs=dict(rfs),
                          terminate=terminating_sccs[:],
                          nonterminate=nonterminating_sccs[:],
                          unknown_sccs=maybe_sccs[:],
                          graph=original_cfg)
    return response

def analyse_scc_nontermination(algs, scc, close_walk_depth=5):
    cw_algs = [a for a in algs if a.use_close_walk()]
    nt_algs = [a for a in algs if not a.use_close_walk()]

    if len(cw_algs) > 0:
        for cw in scc.get_close_walks(close_walk_depth):
            OM.printif(1, "\nAnalysing Close Walk: {}.".format([t["name"] for t in cw]))
            for a in cw_algs:
                response = a.run(scc, cw)
                if response.get_status().is_nonterminate():
                    return response
    if len(nt_algs) > 0:
        for a in nt_algs:
            response = a.run(scc)
            if response.get_status().is_nonterminate():
                return response
    return False

def analyse_scc_termination(algs, cfg, dt_modes=[False]):
    trans = cfg.get_edges()
    nodes = ', '.join(sorted(cfg.get_nodes()))
    trs = ', '.join(sorted([t["name"] for t in trans]))
    answer = Result()
    OM.printif(1, "SCC\n+-- Transitions: {}\n+-- Nodes: {}".format(trs, nodes))
    if not trans:
        answer.set_response(status=TerminationResult.TERMINATE,
                            info="No transitions")
        OM.printif(1, "-> Ranked because it has not transitions.")
        return answer
    if not cfg.has_cycle():
        answer.set_response(status=TerminationResult.TERMINATE,
                            info="No cycles.")

        OM.printif(1, "-> Ranked because it has not cycles.")
        return answer

    for dt in dt_modes:
        if dt:
            OM.printif(1, "- Using Different Template")
        R = run_algs(algs, cfg, different_template=dt)
        if R.has("info"):
            OM.printif(1, R.get("info"))
        if R.get_status().is_terminate():
            OM.printif(2, "--> Found with dt={}.\n".format(dt))
            OM.printif(1, R.toStrRankingFunctions(cfg.get_info("global_vars")))
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
        OM.printif(1, "--> with: " + str(alg))

        R = alg.run(cfg,
                    different_template=different_template)

        OM.printif(3, R.debug())
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



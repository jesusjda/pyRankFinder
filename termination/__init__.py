from .algorithm import NonTermination_Algorithm_Manager
from .algorithm import Termination_Algorithm_Manager
from .output import Output_Manager
from .result import Result
from .result import TerminationResult
from .algorithm.utils import showgraph
from nodeproperties import compute_invariants
from partialevaluation import control_flow_refinement
from partialevaluation import prepare_scc
from .algorithm.utils import compute_way_nodes

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
    if config["different_template"] == "always":
        dt_modes = [True]
    elif config["different_template"] == "iffail":
        dt_modes = [False, True]
    else:
        dt_modes = [False]
    cfr, cfr_before, cfr_scc, cfr_after = prepare_cfr_config(config)
    max_sccd = config["scc_depth"]
    fast_answer = config["stop_if_fail"]
    cfg.build_polyhedrons()
    rmded = cfg.remove_unsat_edges()
    if len(rmded) > 0:
        OM.printif(1, "Removed edges {} because they where unsat.".format(rmded))
    showgraph(cfg, config, sufix="", console=config["print_graphs"], writef=False, output_formats=["fc", "svg"])
    from .algorithm.utils import merge
    rfs = {}
    maybe_sccs = []
    terminating_sccs = []
    nonterminating_sccs = []
    stop_all = False
    original_cfg = cfg

    compute_invariants(cfg, abstract_domain=config["invariants"],
                       threshold_modes=config["invariants_threshold"],
                       add_to_polyhedron=True)
    if cfr_before:
        cfg = control_flow_refinement(cfg, cfr)
        compute_invariants(cfg, abstract_domain=config["invariants"],
                           threshold_modes=config["invariants_threshold"],
                           add_to_polyhedron=True)
        showgraph(cfg, config, sufix="cfr_before", console=config["print_graphs"], writef=False, output_formats=["fc", "svg"])
    # cfr loop
    cfr_it = -1
    CFGs = [(cfg, max_sccd, 0)]
    while (not stop_all):
        cfr_it += 1
        stop = False
        do_cfr_after = cfr_after and cfr_it < cfr["cfr_max_tries"]
        # SCC splitting and analysis
        while (not stop and CFGs):
            current_cfg, sccd, cfr_num = CFGs.pop(0)
            removed = current_cfg.remove_unsat_edges()
            if len(removed) > 0:
                OM.printif(2, "Transition (" + str(removed) + ") were removed because it is empty.")
            if len(current_cfg.get_edges()) == 0:
                OM.printif(2, "This graph has not transitions.")
                OM.printif(2, "|-- nodes: {}".format(current_cfg.get_nodes()))
                continue
            cfg_cfr = current_cfg
            if cfr_scc and cfr_num > 0:
                cfg_cfr = control_flow_refinement(prepare_scc(cfg, current_cfg, config["invariants"]), cfr)
            CFGs_aux = cfg_cfr.get_scc() if sccd > 0 else [cfg_cfr]
            sccd -= 1

            can_be_terminate = len(t_algs) > 0
            can_be_nonterminate = len(nt_algs) > 0
            do_cfr_scc = cfr_scc and cfr_num < cfr["cfr_max_tries"]
            while CFGs_aux:
                scc = CFGs_aux.pop(0)
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
                                maybe_sccs += CFGs_aux
                                maybe_sccs += [s for s, __, __ in CFGs]
                                break  # NO!
                            continue
                    if do_cfr_scc:
                        CFGs = [(scc, max_sccd, cfr_num + 1)] + CFGs
                    else:
                        maybe_sccs.append(scc)
                        if do_cfr_after:
                            OM.printif(1, "ONE SCC waiting for cfr after")
                        elif fast_answer and not can_be_nonterminate:
                            stop = True
                            maybe_sccs += CFGs_aux
                            break  # MAYBE!
                else:
                    R.set_response(graph=scc)
                    terminating_sccs.append(R)
                    if R.has("pending_trs"):
                        pending_trs = R.get("pending_trs")
                        if pending_trs:
                            CFGs = [(cfg.edge_data_subgraph(pending_trs),
                                     sccd, cfr_num)] + CFGs
                    if R.has("rfs"):
                        merge(rfs, R.get("rfs"))
                    continue
        # Cfr after
        if not stop_all and len(maybe_sccs) > 0 and do_cfr_after:
            important_nodes = []
            heads = []
            for scc in maybe_sccs:
                important_nodes += scc.get_nodes()
                heads += scc.get_info("entry_nodes")
            OM.printif(1, "CFR after")
            OM.printif(2, "Nodes to refine:", important_nodes)
            way_nodes = compute_way_nodes(cfg, heads)
            OM.printif(3, "Nodes on the way:", way_nodes)
            cfg.remove_nodes_from([n for n in cfg.get_nodes() if n not in way_nodes])
            cfg = control_flow_refinement(cfg, cfr, only_nodes=important_nodes)
            new_important_nodes = [n for n in cfg.get_nodes() for n1 in important_nodes if "n_" + n1 == n[:len(n1) + 2]]
            compute_invariants(cfg, abstract_domain=config["invariants"], threshold_modes=config["invariants_threshold"],
                               add_to_polyhedron=True)
            OM.printif(3, "Important nodes from the cfr graph:", new_important_nodes)
            showgraph(cfg, config, sufix="cfr_after_" + str(cfr_it), console=config["print_graphs"],
                      writef=False, output_formats=["fc", "svg"])
            if len(new_important_nodes) == 0:
                stop_all = True
                break  # MAYBE!
            set_new_important_nodes = set(new_important_nodes)
            new_sccs = []
            for scc in cfg.get_scc():
                if len(scc.get_edges()) == 0:
                    continue
                if set(scc.get_nodes()) <= set_new_important_nodes:
                    new_sccs.append((scc, max_sccd, 0))
            maybe_sccs = []
            CFGs = new_sccs + CFGs
        else:
            stop_all = True

    status = TerminationResult.UNKNOWN
    if can_be_nonterminate and len(nonterminating_sccs) > 0:
        status = TerminationResult.NONTERMINATE
    elif len(maybe_sccs) > 0:
        status = TerminationResult.UNKNOWN
    elif can_be_terminate:
        status = TerminationResult.TERMINATE
    response = Result()
    response.set_response(status=status,
                          rfs=dict(rfs),
                          terminate=terminating_sccs[:],
                          nonterminate=nonterminating_sccs[:],
                          unknown_sccs=maybe_sccs[:],
                          graph=original_cfg)
    return response


def prepare_cfr_config(config):
    cfr = {"cfr_iterations": 0, "cfr_max_tries": 0}
    cfr_scc = config["cfr_strategy_scc"]
    cfr_after = config["cfr_strategy_after"]
    cfr_before = config["cfr_strategy_before"]
    if cfr_scc or cfr_after or cfr_before:
        cfr = {
            "cfr_iterations": config["cfr_iterations"],
            "cfr_invariants": config["cfr_invariants"],
            "invariants": config["invariants"],
            "invariants_threshold": config["invariants_threshold"],
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
    return cfr, cfr_before, cfr_scc, cfr_after


def analyse_scc_nontermination(algs, scc, close_walk_depth=5):
    cw_algs = [a for a in algs if a.use_close_walk()]
    nt_algs = [a for a in algs if not a.use_close_walk()]
    if len(nt_algs) > 0:
        for a in nt_algs:
            response = a.run(scc)
            if response.get_status().is_nonterminate():
                return response
    if len(cw_algs) > 0:
        for cw in scc.get_close_walks(close_walk_depth):
            OM.printif(1, "\nAnalysing Close Walk: {}.".format([t["name"] for t in cw]))
            for a in cw_algs:
                response = a.run(scc, cw)
                if response.get_status().is_nonterminate():
                    return response
    return False


def analyse_scc_termination(algs, cfg, dt_modes=[False]):
    trans = cfg.get_edges()
    answer = Result()
    OM.lazy_printif(1, lambda: "SCC\n+-- Transitions: {}\n+-- Nodes: {}".format(', '.join(sorted([t["name"] for t in trans])),
                                                                                ', '.join(sorted(cfg.get_nodes()))))
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
            OM.lazy_printif(1, lambda: R.get("info"))
        if R.get_status().is_terminate():
            OM.printif(2, "--> Found with dt={}.\n".format(dt))
            OM.lazy_printif(1, lambda: R.toStrRankingFunctions(cfg.get_info("global_vars")))
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

        OM.lazy_printif(3, R.debug)
        if R.get_status().is_terminate():
            if R.get("rfs"):
                f = True
                break
    if f:
        pending = []
        if R.has("pending_trs"):
            pending = R.get("pending_trs")
        response.set_response(status=TerminationResult.TERMINATE,
                              info="Found",
                              rfs=R.get("rfs"),
                              pending_trs=pending)
        return response

    response.set_response(status=TerminationResult.UNKNOWN,
                          info="Not Found")
    return response

from .abstractStates import state
from .thresholds import compute_thresholds

__all__ = ["compute_reachability"]


def compute_reachability(cfg, abstract_domain="polyhedra", widening_frecuency=3, threshold_modes=[], user_props=False, init_nodes=[]):
    from lpi import C_Polyhedron
    graph_nodes = cfg.get_nodes(data=True)

    threshold = compute_thresholds(cfg, modes=threshold_modes)
    nodes = {}
    global_vars = cfg.get_info("global_vars")
    Nvars = int(len(global_vars) / 2)
    vars_ = global_vars[:Nvars]
    if(abstract_domain is None or abstract_domain == "none"):
        rechability = {node: state(vars_) for node in graph_nodes}
    else:
        nodes = {}
        queue = []
        for node, node_data in graph_nodes:
            if user_props and "reachability" in node_data:
                st = state(C_Polyhedron(constraints=[c for c in node_data["reachability"] if c.is_linear()],
                                        variables=vars_),
                           abstract_domain=abstract_domain)
                queue.append(node)
            elif node in init_nodes:
                st = state(vars_, abstract_domain=abstract_domain)
                queue.append(node)
            else:
                st = state(vars_, bottom=True, abstract_domain=abstract_domain)
            nodes[node] = {"state": st, "accesses": 0}
        while len(queue) > 0:
            original_states = {}
            while len(queue) > 0:
                node = queue.pop()
                for t in cfg.get_edges(target=node):
                    s = nodes[node]["state"]
                    dest_s = nodes[t["source"]]
                    if not(t["source"] in original_states):
                        original_states[t["source"]] = dest_s["state"]
                    s1 = s.apply_backward_tr(t, copy=True)
                    s2 = dest_s["state"].lub(s1, copy=True)
                    dest_s["state"] = s2
            for node in original_states:
                if not(nodes[node]["state"] <= original_states[node]):
                    nodes[node]["accesses"] += 1
                    if nodes[node]["accesses"] >= widening_frecuency:
                        if len(threshold[node]) > 0:
                            nodes[node]["state"].widening(original_states[node], threshold=threshold[node])
                        else:
                            nodes[node]["state"].widening(original_states[node])
                        nodes[node]["accesses"] = 0
                    queue.append(node)
        rechability = {node: nodes[node]["state"] for node in sorted(nodes)}
    cfg.set_nodes_info(rechability, "reachability_" + str(abstract_domain))
    return rechability

from invariants.polyhedraabstractstate import PolyhedraState
from invariants.intervalabstractstate import IntervalState
from invariants import compute_threshold
__all__ = ["compute_reachability"]

def compute_reachability(cfg, abstract_domain="polyhedra", widening_frecuency=3, use_threshold=False):
    from lpi import C_Polyhedron
    from ppl import Constraint_System
    graph_nodes = cfg.get_nodes(data=True)
    
    threshold = compute_threshold(cfg, use_threshold)
    nodes = {}
    global_vars = cfg.get_info("global_vars")
    Nvars = len(global_vars)/2
    if(abstract_domain is None or abstract_domain == "none"):
        rechability = {node: PolyhedraState(Nvars) for node in graph_nodes}
    else:
        def state(n, bottom=False):
            if abstract_domain.lower() == "polyhedra":
                return PolyhedraState(n, bottom=bottom)
            elif abstract_domain.lower() == "interval":
                return IntervalState(n, bottom=bottom)
            else:
                raise NotImplementedError("{} state type is NOT implemented.".format(abstract_domain))
        nodes = {}
        queue = []
        for node, node_data in graph_nodes:
            if "rechability" in node_data:
                st = state(C_Polyhedron(Constraint_System([c.transform(global_vars, lib="ppl") 
                                                           for c in node_data["rechability"]
                                                           if c.is_linear()]), dim=Nvars))
                queue.append(node)
            else:
                st = state(Nvars, bottom=True)
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
                        #print("WIDENING", node)
                        if use_threshold:
                            nodes[node]["state"].widening(original_states[node], threshold=threshold[node])
                        else:
                            nodes[node]["state"].widening(original_states[node])
                        nodes[node]["accesses"] = 0
                    queue.append(node)
        rechability = {node: nodes[node]["state"] for node in sorted(nodes)}
    cfg.set_nodes_info(rechability, "reachability_"+str(abstract_domain))
    return rechability

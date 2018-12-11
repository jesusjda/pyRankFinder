
__all__ = ["user_invariants", "compute_invariants"]
from .thresholds import user_thresholds
from .abstractStates import state

def use_invariants(cfg, invariant_type):
    from lpi.Lazy_Polyhedron import C_Polyhedron
    inv_name = "invariant_"+str(invariant_type)
    edges = cfg.get_edges()
    Nvars = len(cfg.get_info("global_vars"))
    for e in edges:
        Nlocal_vars = len(e["local_vars"])
        tr_cons = e["tr_polyhedron"].get_constraints()
        try:
            inv = cfg.nodes[e["source"]][inv_name].get_constraints()
        except:
            inv = []
        tr_poly = C_Polyhedron(dim=Nvars+Nlocal_vars)
        for c in tr_cons:
            tr_poly.add_constraint(c)
        for c in inv:
            tr_poly.add_constraint(c)
        cfg.set_edge_info(source=e["source"], target=e["target"], name=e["name"],
                          key="polyhedron", value=tr_poly)

def user_invariants(cfg):
    raise NotImplementedError("User invariants is not implemented yet.")


def compute_invariants(cfg, abstract_domain="polyhedra", widening_frecuency=3, use_threshold=False, add_to_polyhedron=False):
    cfg.build_polyhedrons()
    graph_nodes = cfg.get_nodes()
    init_node = cfg.get_info("init_node")
    threshold = user_thresholds(cfg, use_threshold)
    nodes = {}
    global_vars = cfg.get_info("global_vars")
    Nvars = len(global_vars)/2
    if(abstract_domain is None or abstract_domain == "none"):
        invariants = {node: state(Nvars) for node in graph_nodes}
    else:
        nodes = {node:{"state": state(Nvars, bottom=True, abstract_domain=abstract_domain), "accesses": 0}
                 for node in graph_nodes}
        nodes[init_node]["state"] = state(Nvars, abstract_domain=abstract_domain)
        from termination.output import Output_Manager as OM
        queue = [init_node]
        while len(queue) > 0:
            original_states = {}
            while len(queue) > 0:
                node = queue.pop()
                for t in cfg.get_edges(source=node):
                    s = nodes[node]["state"]
                    dest_s = nodes[t["target"]]
                    OM.printif(4,t["target"], dest_s["state"])
                    if not(t["target"] in original_states):
                        original_states[t["target"]] = dest_s["state"]
                    s1 = s.apply_tr(t, copy=True)
                    OM.printif(4,"apply {}".format(t["name"]), t["tr_polyhedron"].get_constraints(), s1)
                    s2 = dest_s["state"].lub(s1, copy=True)
                    OM.printif(4,"lub", s2)
                    dest_s["state"] = s2
            OM.printif(4,"---")
            for node in original_states:
                if not(nodes[node]["state"] <= original_states[node]):
                    nodes[node]["accesses"] += 1
                    if nodes[node]["accesses"] >= widening_frecuency:
                        OM.printif(4, "WIDENING", node)
                        if use_threshold:
                            nodes[node]["state"].widening(original_states[node], threshold=threshold[node])
                        else:
                            nodes[node]["state"].widening(original_states[node])
                        OM.printif(4,"result: ", nodes[node]["state"])
                        nodes[node]["accesses"] = 0
                    queue.append(node)
        invariants = {node: nodes[node]["state"] for node in sorted(nodes)}
    cfg.set_nodes_info(invariants, "invariant_"+str(abstract_domain))
    if add_to_polyhedron:
        OM.printseparator(1)
        OM.printif(1, "INVARIANTS ({})".format(abstract_domain))
        gvars = cfg.get_info("global_vars")
        OM.printif(1, "\n".join(["-> " + str(n) + " = " +
                                 str(invariants[n].toString(gvars))
                                 for n in sorted(invariants)]))
        OM.printseparator(1)
        use_invariants(cfg, abstract_domain)
    return invariants
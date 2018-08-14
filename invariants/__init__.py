
from .abstractdomain import AbstractDomain
from .abstractstate import PolyhedraState
from .abstractstate import IntervalState

__all__ = ["compute_invariants"]

def compute_invariants(cfg, invariant_type="polyhedra"):
    graph_nodes = cfg.nodes()
    nodes = {}
    global_vars = cfg.get_info("global_vars")
    Nvars = len(global_vars)/2
    if(invariant_type is None or invariant_type == "none"):
        nodes = {node:{"state": PolyhedraState(Nvars)} for node in graph_nodes}
    else:
        def state(n, bottom=False):
            if invariant_type.lower() == "polyhedra":
                return PolyhedraState(n, bottom=bottom)
            elif invariant_type.lower() == "interval":
                return IntervalState(n, bottom=bottom)
            else:
                raise NotImplementedError("Invariants {} are not implemented.".format(invariant_type))

        init_node = cfg.get_info("init_node")

        nodes = {node:{"state": state(Nvars, bottom=True), "accesses": 0}
                 for node in graph_nodes}

        nodes[init_node]["state"] = state(Nvars)

        queue = [init_node]
        while len(queue) > 0:
            node = queue.pop()
            s = nodes[node]["state"]
            for t in cfg.get_edges(source=node):
                dest_s = nodes[t["target"]]
                s1 = s.apply_tr(t, copy=True)
                s2 = dest_s["state"].lub(s1, copy=True)
                if not(s2 <= dest_s["state"]):  # lte(s2, dest_s["state"]):
                    dest_s["accesses"] += 1
                    if dest_s["accesses"] >= 3:
                        s2.widening(dest_s["state"])
                        dest_s["accesses"] = 0
                    dest_s["state"] = s2
                    if not(t["target"] in queue):
                        queue.append(t["target"])
    return {node: nodes[node]["state"] for node in nodes}

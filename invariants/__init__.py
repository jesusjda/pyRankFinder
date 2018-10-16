from copy import deepcopy

__all__ = ["compute_invariants", "compute_rechability"]


class AbstractState(object):

    def __init__(self, arg1, bottom=False):
        raise Exception("Abstract State")

    def _assert_same_type(self, s):
        if not(type(self) is type(s)):
            raise TypeError("Not same type of State")

    def copy(self, copy=True):
        if copy:
            return deepcopy(self)
        else:
            return self

    def lub(self, s2, copy=False):
        pass

    def widening(self, s2, threshold=None, copy=False):
        if threshold is not None:
            print("state widening with threshold")
            print(s2, threshold)
            self.extrapolation_assign(s2, threshold, copy)
        else:
            #print("state widening")
            self.widening_assign(s2, copy)

    def apply_tr(self, tr, copy=False):
        pass

    def get_constraints(self):
        pass

    def __le__(self, s2):
        pass

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def __repr__(self):
        return "{{{}}}".format(", ".join(self.toString()))


def compute_threshold(cfg, use_threshold=False):
    if not use_threshold:
        return {n:None for n in cfg.get_nodes()}
    from ppl import Constraint_System
    node_data = cfg.get_nodes(data=True)
    threshold = {}
    gvars = cfg.get_info("global_vars")
    for node, data in node_data:
        if "threshold" in data:
            cs = Constraint_System([c.transform(gvars, lib="ppl") 
                                    for c in data["threshold"]
                                    if c.is_linear()])
        else:
            cs = Constraint_System()
        threshold[node] = cs
    cfg.set_nodes_info(threshold, "cs_threshold")
    return threshold

from invariants.polyhedraabstractstate import PolyhedraState
from invariants.intervalabstractstate import IntervalState


def compute_invariants(cfg, invariant_type="polyhedra", widening_frecuency=3, use_threshold=False):
    from ppl import Constraint_System
    graph_nodes = cfg.get_nodes()
    init_node = cfg.get_info("init_node")
    threshold = compute_threshold(cfg, use_threshold)
    nodes = {}
    global_vars = cfg.get_info("global_vars")
    Nvars = len(global_vars)/2
    if(invariant_type is None or invariant_type == "none"):
        invariants = {node: PolyhedraState(Nvars) for node in graph_nodes}
    else:
        def state(n, bottom=False):
            if invariant_type.lower() == "polyhedra":
                return PolyhedraState(n, bottom=bottom)
            elif invariant_type.lower() == "interval":
                return IntervalState(n, bottom=bottom)
            else:
                raise NotImplementedError("{} state type is NOT implemented.".format(invariant_type))
        nodes = {node:{"state": state(Nvars, bottom=True), "accesses": 0}
                 for node in graph_nodes}

        nodes[init_node]["state"] = state(Nvars)

        queue = [init_node]
        while len(queue) > 0:
            original_states = {}
            while len(queue) > 0:
                node = queue.pop()
                for t in cfg.get_edges(source=node):
                    s = nodes[node]["state"]
                    dest_s = nodes[t["target"]]
                    if not(t["target"] in original_states):
                        original_states[t["target"]] = dest_s["state"]
                    s1 = s.apply_tr(t, copy=True)
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
        invariants = {node: nodes[node]["state"] for node in sorted(nodes)}
    cfg.set_nodes_info(invariants, "invariant_"+str(invariant_type))
    return invariants

from invariants.rechability import compute_rechability

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

from copy import deepcopy


__all__ = ["compute_invariants"]


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

    def widening(self, s2, copy=False):
        pass

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


from invariants.polyhedraabstractstate import PolyhedraState
from invariants.intervalabstractstate import IntervalState


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

    for node in nodes:
        cfg.nodes[node]["invariant_"+str(invariant_type)] = nodes[node]["state"] 
    return {node: nodes[node]["state"] for node in sorted(nodes)}


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

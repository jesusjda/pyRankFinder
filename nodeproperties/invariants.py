
__all__ = ["invariant"]
from .thresholds import compute_thresholds
from .assertions import check_assertions
from .abstractStates import state


class Invariants:

    def __init__(self, config={}):
        self.conf = {
            "widening_frequency": 3,
            "widening_nodes_mode": "all",
            "widening_nodes": None,
            "abstract_domain": "polyhedra",
            "threshold_modes": False
        }
        self.set_configuration(config)

    def set_configuration(self, config):
        for k in self.conf:
            if k in config:
                self.conf[k] = config[k]
            elif "invariant_" + k in config:
                self.conf[k] = config["invariant_" + k]
        if "invariants" in config:
            self.conf["abstract_domain"] = config["invariants"]
        if "invariant_widening_nodes" in config:
            self.conf["widening_nodes"] = config["invariant_widening_nodes"]
        if "invariants_threshold" in config:
            self.conf["threshold_modes"] = config["invariants_threshold"]
        if self.conf["widening_nodes_mode"] not in ["all", "user", "cyclecutnodes"]:
            raise ValueError("Invalid value ({}) for the parameter widening_nodes_mode.".format(self.conf["widening_nodes_mode"]))

    def use_invariants(self, cfg, invariant_type):
        inv_name = "invariant_" + str(invariant_type)
        edges = cfg.get_edges()
        for e in edges:
            try:
                inv = cfg.nodes[e["source"]][inv_name].get_constraints()
            except Exception:
                inv = []
            tr_poly = e["polyhedron"].copy()
            tr_poly.add_constraints(inv)
            cfg.set_edge_info(source=e["source"], target=e["target"], name=e["name"],
                              key="polyhedron", value=tr_poly)

    def user_invariants(self, cfg):
        raise NotImplementedError("User invariants is not implemented yet.")

    def get_widening_nodes(self, cfg):
        widening_nodes_mode = self.conf["widening_nodes_mode"]
        all_nodes = list(cfg.get_nodes())
        if widening_nodes_mode == "all":
            return True, all_nodes
        if widening_nodes_mode == "cyclecutnodes":
            cc_nodes = cfg.cycle_cut_nodes()
            return len(cc_nodes) == len(all_nodes), cc_nodes
        if widening_nodes_mode == "user":
            return False, list(self.conf["widening_nodes"])

    def compute_invariants(self, cfg, check=False, add_to_polyhedron=False):
        from termination.output import Output_Manager as OM
        abstract_domain = self.conf["abstract_domain"]
        threshold_modes = self.conf["threshold_modes"]
        widening_frequency = self.conf["widening_frequency"]
        graph_nodes = cfg.get_nodes()
        global_vars = cfg.get_info("global_vars")
        Nvars = int(len(global_vars) / 2)
        vars_ = global_vars[:Nvars]
        from lpi import C_Polyhedron
        if(abstract_domain is None or abstract_domain == "none"):
            invariants = {node: state(vars_) for node in graph_nodes}
        else:
            do_wide_always, widening_nodes = self.get_widening_nodes(cfg)
            if not do_wide_always:
                OM.printif(1, "List of nodes where to apply widening (with frequency {}): {}".format(widening_frequency, widening_nodes))
            cfg.build_polyhedrons()
            init_node = cfg.get_info("init_node")
            threshold = compute_thresholds(cfg, modes=threshold_modes)
            nodes = {}
            nodes = {node: {"state": state(vars_, bottom=True, abstract_domain=abstract_domain), "accesses": 0}
                     for node in graph_nodes}
            nodes[init_node]["state"] = state(vars_, abstract_domain=abstract_domain)
            queue = [init_node]
            while len(queue) > 0:
                original_states = {}
                while len(queue) > 0:
                    node = queue.pop()
                    for t in cfg.get_edges(source=node):
                        s = nodes[node]["state"]
                        dest_s = nodes[t["target"]]
                        OM.printif(4, t["target"], dest_s["state"])
                        if not(t["target"] in original_states):
                            original_states[t["target"]] = dest_s["state"]
                        s1 = s.apply_tr(t, copy=True)
                        OM.printif(4, "apply {}".format(t["name"]), t["polyhedron"], s1)
                        s2 = dest_s["state"].lub(s1, copy=True)
                        OM.printif(4, "lub", s2)
                        dest_s["state"] = s2
                OM.printif(4, "---")
                for node in original_states:
                    if not(nodes[node]["state"] <= original_states[node]):
                        nodes[node]["accesses"] += 1
                        if nodes[node]["accesses"] >= widening_frequency and (do_wide_always or node in widening_nodes):
                            OM.printif(4, "WIDENING", node)
                            if len(threshold[node]) > 0:
                                nodes[node]["state"].widening(original_states[node], threshold=threshold[node])
                            else:
                                nodes[node]["state"].widening(original_states[node])
                            OM.printif(4, "result: ", nodes[node]["state"])
                            nodes[node]["accesses"] = 0
                        queue.append(node)
            invariants = {node: C_Polyhedron(nodes[node]["state"].get_constraints(), vars_) for node in sorted(nodes)}
        cfg.set_nodes_info(invariants, "invariant_" + str(abstract_domain))
        if check or add_to_polyhedron:
            OM.printseparator(1)
            OM.lazy_printif(1, lambda: "INVARIANTS ({})\n".format(abstract_domain),
                            lambda: "\n".join(["-> " + str(n) + " = " + str(invariants[n].get_constraints())
                                               for n in sorted(invariants)]))
            OM.printseparator(1)
        if add_to_polyhedron:
            self.use_invariants(cfg, abstract_domain)
        check_assertions(cfg, abstract_domain, do=check)
        return invariants


invariant = Invariants()

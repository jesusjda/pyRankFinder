from termination.output import Output_Manager as OM
from .abstractStates import state as absState


def check_assertions(cfg, abstract_domain="polyhedra", do=True):
    def state(A, abstract_domain):
        if abstract_domain == "polyhedra":
            return A
        else:
            st = absState(A,abstract_domain=abstract_domain)
            return C_Polyhedron(st.get_constraints())
        
    if not do or abstract_domain is None or abstract_domain == "none":
        return True
    from lpi import C_Polyhedron
    from ppl import Constraint_System
    graph_nodes = cfg.get_nodes(data=True)
    global_vars = cfg.get_info("global_vars")
    Nvars = len(global_vars)/2
    correct = True
    for node, node_data in graph_nodes:
        if "asserts" in node_data and node_data["asserts"]:
            OM.printif(1, "Checking asserts of node {}".format(node))
            inv = C_Polyhedron(node_data["invariant_"+abstract_domain].get_constraints())
            node_correct = True
            for asert in node_data["asserts"]:
                st = state(C_Polyhedron(Constraint_System([c.transform(global_vars, lib="ppl") 
                                                           for c in asert
                                                           if c.is_linear()]), dim=Nvars),
                           abstract_domain=abstract_domain)
                if not st.contains(inv):
                    OM.printf("Assertion Fail at node {}:\n{} no include {}".format(node, st, inv))
                    correct = False
                    node_correct = False
            if node_correct:
                OM.printif(1, "Correct!")
    if correct:
        OM.printf("The invariants ({}) hold into the asserts!".format(abstract_domain))
    return correct
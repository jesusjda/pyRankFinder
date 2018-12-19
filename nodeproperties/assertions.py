from termination.output import Output_Manager as OM
from .abstractStates import state as absState


def check_assertions(cfg, abstract_domain="polyhedra", do=True):
    def state(A, abstract_domain, dim):
        if abstract_domain == "polyhedra":
            return A
        else:
            st = absState(A, abstract_domain=abstract_domain)
            return C_Polyhedron(st.get_constraints(), dim=dim)
        
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
            OM.printf("- Checking asserts of node {}".format(node))
            try:
                inv = C_Polyhedron(node_data["invariant_"+abstract_domain].get_constraints(), dim=Nvars)
            except:
                inv = C_Polyhedron(dim=Nvars)
            node_correct = len(node_data["asserts"]) == 0
            for disjunction in node_data["asserts"]:
                for conjunction in disjunction:
                    st = state(C_Polyhedron(Constraint_System([c.transform(global_vars, lib="ppl")
                                                               for c in conjunction
                                                               if c.is_linear()]), dim=Nvars),
                               abstract_domain=abstract_domain, dim=Nvars)
                    if st.contains(inv):
                        node_correct = True
                        break
                if node_correct:
                    break
            if node_correct:
                OM.printf("- - Correct!")
            else:
                OM.printf("- - {} invariant doesn't hold!".format(node))
                correct = False
    if correct:
        OM.printf("- All the invariants ({}) hold into the asserts!".format(abstract_domain))
    else:
        OM.printf("- There where some invariants ({}) where it fails!".format(abstract_domain))
    return correct

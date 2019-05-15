from genericparser import constants as gconsts


def check_assertions(cfg, abstract_domain="polyhedra", do=True):
    from termination.output import Output_Manager as OM
    if not do or abstract_domain is None or abstract_domain == "none":
        return True
    from lpi import C_Polyhedron
    graph_nodes = cfg.get_nodes(data=True)
    global_vars = cfg.get_info(gconsts.variables)
    Nvars = int(len(global_vars) / 2)
    vars_ = global_vars[:Nvars]
    correct = True
    for node, node_data in graph_nodes:
        if node_data.get(gconsts.node.assertions, []):
            OM.printf("- Checking asserts of node {}".format(node))
            try:
                inv = node_data["invariant_" + abstract_domain]
            except Exception:
                inv = C_Polyhedron(variables=vars_)
            node_correct = len(node_data[gconsts.node.assertions]) == 0
            for disjunction in node_data[gconsts.node.assertions]:
                for conjunction in disjunction:
                    st = C_Polyhedron([c for c in conjunction if c.is_linear()],
                                      variables=vars_)
                    if st >= inv:
                        node_correct = True
                        break
                if node_correct:
                    break
            if node_correct:
                OM.printf("- - Correct!")
            else:
                OM.printf("- - invariant: {}\n- - asserts: {}".format(inv.get_constraints(), node_data["asserts"]))
                OM.printf("- - DOESN'T HOLD!".format(node))
                correct = False
    if correct:
        OM.printf("- All the invariants ({}) hold into the asserts!".format(abstract_domain))
    else:
        OM.printf("- There where some invariants ({}) where it fails!".format(abstract_domain))
    OM.printseparator(0)
    return correct

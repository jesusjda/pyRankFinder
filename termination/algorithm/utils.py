def max_dim(edges):
    maximum = 0
    for e in edges:
        d = e["polyhedron"].get_dimension()
        d -= len(e["local_vars"])
        if d > maximum:
            maximum = d
    return maximum


def get_rf(variables, point):
    """
    Assume variables[0] is the independent term
    the result point has as coord(0) the indep term
    """
    from ppl import Linear_Expression
    from ppl import Variable
    from ppl import point as pplpoint
    exp = Linear_Expression(0)
    for i in range(len(variables)):
        exp += point.coefficient(variables[i])*Variable(i)
    return pplpoint(exp)


def get_use_z3(algorithm, use_z3=None):
    if use_z3 is None:
        if "lib" in algorithm:
            return algorithm["lib"] == "z3"
        return False
    else:
        return use_z3


def get_ppl_transition_polyhedron(tr, global_vars):
    from ppl import Constraint_System
    from lpi import C_Polyhedron
    local_vars = tr["local_vars"]
    dim = len(global_vars)+len(local_vars)
    all_vars = global_vars + local_vars
    cons = tr["constraints"]
    constrs = [c.transform(all_vars, lib="ppl")
               for c in cons if c.is_linear()]
    tr_poly = C_Polyhedron(Constraint_System(constrs), dim)
    return tr_poly

def get_z3_transition_polyhedron(tr, global_vars):
    local_vars = tr["local_vars"]
    all_vars = global_vars + local_vars
    cons = tr["constraints"]
    constrs = [c.transform(all_vars, lib="z3")
               for c in cons]
    return constrs

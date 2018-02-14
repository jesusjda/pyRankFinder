from ppl import Linear_Expression
from ppl import Variable
from ppl import point as pplpoint


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


def str_to_constraint(text, vars, pvars, use_z3=True):
    if use_z3:
        from z3 import Real
    
    
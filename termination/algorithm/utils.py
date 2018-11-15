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


def get_z3_transition_polyhedron(tr, global_vars):
    local_vars = tr["local_vars"]
    all_vars = global_vars + local_vars
    cons = tr["constraints"]
    constrs = [c.transform(all_vars, lib="z3")
               for c in cons]
    return constrs

def get_ppl_transition_polyhedron(tr, global_vars):
    local_vars = tr["local_vars"]
    all_vars = global_vars + local_vars
    cons = tr["constraints"]
    constrs = [c.transform(all_vars, lib="z3")
               for c in cons]
    return constrs

def generate_names(vs, others):
    names = []
    variables = vs + others
    for v in vs:
        pv = v
        while (pv != v and pv in variables) or pv in names:
            pv += "'"
        names.append(pv)
    return names

def generate_prime_names(vs, others):
    names = []
    variables = vs + others
    for v in vs:
        pv = v + "'"
        while pv in variables or pv in names:
            pv += "'"
        names.append(pv)
    return names

def merge(base, to_add):
    result = base
    for key in to_add:
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(to_add[key])
        else:
            result[key] = [to_add[key]]
    return result
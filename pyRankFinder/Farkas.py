from functools import reduce
from ppl import Variable


def LRF(polyhedron, lambdas, f1, f2):
    """
    f1 >= 0
    f1 - f2 >= 1
    """
    constraints = df(polyhedron, lambdas[0], f1, f2, 1)
    constraints += f(polyhedron, lambdas[1], f1, 0)
    return constraints


def NLRF(polyhedron, lambdas, fs, ft):
    """
    fs[0] - ft[0] >= 1
    (fs[i] - ft[i]) + fs[i-1] >= 1
    fs[d] >= 0
    """
    # fs[0] - ft[0] >= 1
    constraints = df(polyhedron, lambdas[0], fs[0], ft[0], 1)
    # (fs[i] - ft[i]) + fs[i-1] >= 1
    for i in range(1, len(fs)):
        dff = []
        for j in range(len(fs[i])):
            dff.append(fs[i][j] - ft[i][j] + fs[i-1][j])
        constraints += f(polyhedron, lambdas[i], dff, 1)
    # fs[d] >= 0
    constraints += f(polyhedron, lambdas[-1], fs[-1], 0)
    return constraints


def df(polyhedron, lambdas, f1, f2, delta):
    """
    f1 - f2 >= delta
    """
    f2vars = [-v for v in f2[1::]]
    exp = f1[1::] + f2vars
    inh = f1[0] - f2[0] - delta
    return _farkas(polyhedron, lambdas, exp, inh)


def f(polyhedron, lambdas, f, delta):
    """
    f >= delta
    """
    exp = f[1::] + [0 for v in f[1::]]
    inh = f[0] - delta
    return _farkas(polyhedron, lambdas, exp, inh)


def _farkas(polyhedron, lambdas, expressions, inhomogeneous):
    """Returns a list of Constraints, corresponding with the farkas
    constraints for the expressions in `expr`.
    polyhedron of (dimension <= n) with its variables (x1,...,xn)
    polyhedron ==> (e1 x1 + ... + en xn + e0 >= 0)

    :param polyhedron: Polyhedron
    :type polyhedron: `LPi.C_polyhedron`
    :param expressions: [e1,...,en] where ei is a linear expression
    :type expressions: `list` of `ppl.Linear_Expression`
    :param inhomogeneous: e0, expression for the inhomogeneous term
    :type inhomogeneous: `ppl.Linear_Expression`
    :param lambdas: List of lambdas
    :type lambdas: `list` of `ppl.Variable`
    """
    dim = len(expressions)
    cs = polyhedron.get_constraints()
    num_constraints = len(cs)
    constraint_list = []
    # each variable restriction
    for i in range(dim):
        exp = 0
        for j in range(num_constraints):
            exp = exp + cs[j].coefficient(Variable(i)) * lambdas[j]

        constraint_list.append(exp == expressions[i])

    # inhomogeneous restriction
    exp = 0
    for j in range(num_constraints):
        exp = exp + cs[j].inhomogeneous_term() * lambdas[j]
    constraint_list.append(exp - inhomogeneous <= 0)

    # lambda >= 0 restrictions if is inequality
    for j in range(num_constraints):
        if cs[j].is_inequality():
            constraint_list.append(lambdas[j] >= 0)

    return constraint_list

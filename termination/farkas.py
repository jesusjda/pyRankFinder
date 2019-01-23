from lpi import Expression


def LRF(polyhedron, lambdas, f1, f2, d=1):
    """
    f1 >= 0
    f1 - f2 >= 1
    """
    constraints = df(polyhedron, lambdas[0], f1, f2, d)
    constraints += f(polyhedron, lambdas[1], f1, 0)
    return constraints


def QNLRF(polyhedron, lambdas, fs, ft, right=1):
    """
    fs[0] - ft[0] >= right
    (fs[i] - ft[i]) + fs[i-1] >= right
    """
    # fs[0] - ft[0] >= right
    constraints = df(polyhedron, lambdas[0], fs[0], ft[0], right)
    # (fs[i] - ft[i]) + fs[i-1] >= right
    for i in range(1, len(fs)):
        fx = [fs[i][j] + fs[i - 1][j]
              for j in range(len(fs[i]))]
        fxp = ft[i]
        constraints += df(polyhedron, lambdas[i],
                          fx, fxp, right)
    return constraints


def NLRF(polyhedron, lambdas, fs, ft):
    """
    fs[0] - ft[0] >= 1
    (fs[i] - ft[i]) + fs[i-1] >= 1
    fs[d] >= 0
    """
    # fs[0] - ft[0] >= 1
    # (fs[i] - ft[i]) + fs[i-1] >= 1
    constraints = QNLRF(polyhedron, lambdas, fs, ft, 1)
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
    return farkas(polyhedron, lambdas, exp, inh)


def f(polyhedron, lambdas, f, delta):
    """
    f >= delta
    """
    exp = f[1::] + [0 for __ in f[1::]]
    inh = f[0] - delta
    return farkas(polyhedron, lambdas, exp, inh)


def farkas(polyhedron, lambdas, expressions, inhomogeneous):
    """Returns a list of Constraints, corresponding with the farkas
    constraints for the expressions in `expr`.
    polyhedron of (dimension >= n) with its global variables (x1,...,xn)
    and local variables (y1, ...,y(dim-n))
    polyhedron ==> (e1 x1 + ... + en xn + 0 y1 + ... + 0 y(dim-n) + e0 >= 0)
    :param polyhedron: Polyhedron
    :type polyhedron: `lpi.C_polyhedron`
    :param expressions: [e1,...,en] where ei is a linear expression
    :type expressions: `list` of `lpi.Expression`
    :param inhomogeneous: e0, expression for the inhomogeneous term
    :type inhomogeneous: `lpi.Expression`
    :param lambdas: List of lambdas
    :type lambdas: `list` of `lpi.Expression`
    """
    n = len(expressions)
    polyhedron.minimized_constraints()
    vars_ = polyhedron.get_variables()
    cs = polyhedron.get_constraints()
    num_constraints = len(cs)
    constraint_list = []
    i = 0
    for v in vars_:
        exp = Expression(0)
        for j in range(num_constraints):
            exp = exp + cs[j].get_coefficient(v) * lambdas[j]
        if i < n:  # each global variable restriction
            constraint_list.append(exp == expressions[i])
        else:  # local vars restriction
            constraint_list.append(exp == Expression(0))
        i += 1

    # inhomogeneous restriction
    exp = Expression(0)
    for j in range(num_constraints):
        exp = exp + cs[j].get_independent_term() * lambdas[j]
    constraint_list.append(exp - inhomogeneous <= Expression(0))

    # lambda >= 0 restrictions if is inequality
    for j in range(num_constraints):
        if not cs[j].is_equality():
            constraint_list.append(lambdas[j] >= Expression(0))

    return constraint_list

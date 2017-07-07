from functools import reduce
from ppl import Variable


class Farkas:
    
    @staticmethod
    def df(polyhedron, lambdas,
            f1, f2, delta):
        """
        f1 - f2 >= delta
        """
        f2vars = [-v for v in f2[1::]]
        exp = f1[1::] + f2vars
        inh = f1[0] - f2[0] - delta
        return Farkas._farkas(polyhedron, lambdas, exp, inh)

    @staticmethod
    def f(polyhedron, lambdas, f, delta):
        """
        f >= delta
        """
        exp = f[1::] + [0 for v in f[1::]]
        inh = f[0] - delta
        return Farkas._farkas(polyhedron, lambdas, exp, inh)

    @staticmethod
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

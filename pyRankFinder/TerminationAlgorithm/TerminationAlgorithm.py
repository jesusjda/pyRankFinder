from functools import reduce
from ppl import Variable


class TerminationAlgorithm:

    def description(self):
        raise Exception("Not implemented yet!")

    def ranking(self, data):
        raise Exception("Not implemented yet!")

    def print_result(self, result):
        raise Exception("Not implemented yet!")

    def _df_(self, polyhedron, lambdas, vf1, v0f1, vf2=None, v0f2=0):
        """
        """

        if vf2 is None:
            vf2 = vf1
        vf2 = [-v for v in vf2]
        exp = vf1 + vf2
        return self._farkas(polyhedron, lambdas, exp, v0f1 - v0f2)

    def _farkas(self, polyhedron, lambdas, expressions, inhomogeneous):
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
        constraint_list.append(exp + inhomogeneous >= 0)

        # lambda >= 0 restrictions if is inequality
        for j in range(num_constraints):
            if cs[j].is_inequality():
                constraint_list.append(lambdas[j] >= 0)

        return constraint_list

    def _print_function(self, name, Vars, coeffs, size):
        try:
            sr = name + " ( x ) = "
            for i in range(size):
                sr += "" + str(coeffs[i]) + " * " + str(Vars[i]) + " + "
            sr += "" + str(coeffs[size])
            print(sr)
        except Exception as e:
            print("m")

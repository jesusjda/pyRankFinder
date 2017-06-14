from TerminationAlgorithm import *

from ppl import Linear_Expression
from ppl import Variable
from ppl import Constraint_System
from ppl import Constraint
from LPi import C_Polyhedron


class LRFAlgorithm(TerminationAlgorithm):

    _data = {}

    def ranking(self, data):
        self._data = data.copy()
        if not("cfg" in self._data):
            raise Exception(self.__class__+" needs a ControlFlowGraph.")
        cfg = self._data["cfg"]
        edges = cfg.get_edges()

        dim = self._max_dim(edges)
        Nvars = dim / 2
        shifter = 0
        if ("different_template" in self._data and
            self._data["different_template"]):

            shifter = Nvars + 1
        # Calculate rfs vars
        rfvars = {}
        nodeList = {}
        countVar = 0
        for e in edges:
            if not(e["source"] in nodeList):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[e["source"]] = f
                countVar += shifter
            if not(e["target"] in nodeList):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[e["target"]] = f
                countVar += shifter
        countVar += Nvars + 1

        num_constraints = [len(e["tr_polyhedron"].get_constraints())
                           for e in edges]

        lambdas = []
        for Mcons in num_constraints:
            lambdas.append([Variable(k)
                            for k in range(countVar, countVar + Mcons)])
            countVar += Mcons + 1
            lambdas.append([Variable(k)
                            for k in range(countVar, countVar + Mcons)])
            countVar += Mcons + 1

        farkas = []
        it = 0
        for e in edges:
            rf_s = rfvars[e["source"]]
            rf_t = rfvars[e["target"]]
            farkas = farkas + self._f(e["tr_polyhedron"], lambdas[it],
                                      rf_s[1::], rf_s[0],
                                      0)
            it += 1
            farkas = farkas + self._df(e["tr_polyhedron"], lambdas[it],
                                       rf_s[1::], rf_s[0],
                                       rf_t[1::], rf_t[0],
                                       -1)
            it += 1
        poly = C_Polyhedron(Constraint_System(farkas))
        point = poly.get_point()
        if point is None:
            return {'done': False, 'error': "who knows"}
        rfs = {}
        print(point)

        for node in rfvars:
            rfs[node] = ([point.coefficient(c) for c in rfvars[node][1::]],
                         point.coefficient(rfvars[node][0]))
        return {'done': True,
                'rfs': rfs,
                'nvars': Nvars,
                'vars_name': cfg.get_var_name()}

    def _max_dim(self, edges):
        maximum = 0
        for e in edges:
            d = e["tr_polyhedron"].get_dimension()
            if d > maximum:
                maximum = d
        return maximum

    def print_result(self, result):
        if result['done']:
            print(result['rfs'])
            for node in result['rfs']:
                coeffs = result['rfs'][node][0]
                inh = result['rfs'][node][1]
                self._print_function("f_"+node, result['vars_name'],
                                     coeffs, inh)
        else:
            print("ERROR?")

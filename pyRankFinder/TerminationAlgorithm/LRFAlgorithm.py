from TerminationAlgorithm import *

from ppl import Linear_Expression
from ppl import Variable
from ppl import Constraint_System
from ppl import Constraint
from LPi import C_Polyhedron


class LRFAlgorithm(TerminationAlgorithm):


    def ranking(self, cfg):
        self._data = data.copy()
        if not("cfg" in self._data):
            raise Exception(self.__class__+" needs a ControlFlowGraph.")
        cfg = self._data["cfg"]
        transitions = cfg.get_edges()

        dim = self._max_dim(transitions)
        Nvars = dim / 2
        shifter = 0
        if("different_template" in self._data and
           self._data["different_template"]):
            shifter = Nvars + 1
        # farkas Variables
        rfvars = {}
        # farkas constraints
        farkas_constraints = []
        # rfs coefficients (result)
        rfs = {}
        # other stuff
        nodeList = {}
        countVar = 0
        for tr in transitions:
            if not(tr["source"] in nodeList):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["source"]] = f
                countVar += shifter
            if not(tr["target"] in nodeList):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["target"]] = f
                countVar += shifter
        countVar += Nvars + 1

        num_constraints = [len(e["tr_polyhedron"].get_constraints())
                           for e in transitions]

        for tr in transitions:
            rf_s = rfvars[tr["source"]]
            rf_t = rfvars[tr["target"]]
            Mcons = len(tr["tr_polyhedron"].get_constraints())

            # f_s >= 0
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons + 1
            farkas_constraints += self._f(tr["tr_polyhedron"], lambdas,
                                          rf_s, 0)

            # f_s - f_t >= 1
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons + 1
            farkas_constraints += self._df(tr["tr_polyhedron"], lambdas,
                                           rf_s, rf_t, 1)

        poly = C_Polyhedron(Constraint_System(farkas_constraints))
        point = poly.get_point()
        if point is None:
            return {'status': "noRanked", 'error': "who knows"}

        for node in rfvars:
            rfs[node] = ([point.coefficient(c) for c in rfvars[node][1::]],
                         point.coefficient(rfvars[node][0]))
        return {'status': "Ranked",
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
        if result['status'] == "Ranked":
            for node in result['rfs']:
                coeffs = result['rfs'][node][0]
                inh = result['rfs'][node][1]
                self._print_function("f_"+node, result['vars_name'],
                                     coeffs, inh)
        elif result['status'] == "noRanked":
            print("No Found: "+result['status'])
            print(result)
        else:
            print(result)

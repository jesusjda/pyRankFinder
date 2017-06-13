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
        polys = [e["tr_polyhedron"] for e in cfg.get_edges()]
        dim = self._max_dim(polys)
        Nvars = dim / 2
        rfvars = [Variable(i) for i in range(dim)]
        list_constraints = [p.get_constraints() for p in polys]
        num_constraints = [len(cs) for cs in list_constraints]
        lambdas = []
        # different template??
        shift = dim + 1
        for Mcons in num_constraints:
            lambdas.append([Variable(shift+k) for k in range(Mcons)])
            shift = shift + Mcons + 1
        farkas = []
        for i in range(len(polys)):
            farkas = farkas + self._farkas(polys[i], lambdas[i], rfvars, 1)
        print(farkas)
        poly = C_Polyhedron(Constraint_System(farkas))
        point = poly.get_point()
        if point is None:
            return {'done': False, 'error': "who knows"}
        return {'done': True,
                'point': point,
                'nvars': Nvars,
                'cfg': cfg}

    def _max_dim(self, polys):
        maximum = 0
        for p in polys:
            d = p.get_dimension()
            if d > maximum:
                maximum = d
        return maximum

    def print_result(self, result):
        if result['done']:
            V = [Variable(i) for i in range(result['Nvars'])]
            coeffs = [cf for cf in result['point'].coefficients()]
            self._print_function("f", V, coeffs, result['Nvars'])
        else:
            print("ERROR?")

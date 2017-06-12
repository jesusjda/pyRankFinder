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
        list_constraints = [c for p in polys for c in p.get_constraints()]
        num_constraints = len(list_constraints)
        lambdas = [Variable(dim+i) for i in range(0, num_constraints)]
        poly = C_Polyhedron(list_constraints)
        i = 0
        for c in list_constraints:
            if c.is_nonstrict_inequality():
                poly.add_constraint(lambdas[i] >= 0)
            i++
        
        print(poly)

    def _max_dim(self, polys):
        maximum = 0
        for p in polys:
            d = p.get_dimension()
            if d > maximum:
                maximum = d
        return maximum

    def print_result(self, result):
        print(resutl)

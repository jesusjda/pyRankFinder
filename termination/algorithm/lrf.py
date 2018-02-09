from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Variable
from termination import farkas
from termination.result import Result

from .manager import Algorithm
from .manager import Manager
from .utils import get_rf
from .utils import get_use_z3
from .utils import max_dim


class PR(Algorithm):
    ID = "pr"
    NAME = "lrf_pr"
    DESC = "Podelski-Rybalchenko Algorithm for Linear Ranking Functions"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, use_z3=None):
        transitions = cfg.get_edges()

        dim = max_dim(transitions)
        Nvars = int(dim / 2)
        response = Result()
        use_z3 = get_use_z3(self.props, use_z3)
        shifter = 0
        if different_template:
            shifter = Nvars + 1
        # farkas Variables
        rfvars = {}
        # farkas constraints
        farkas_constraints = []
        # rfs coefficients (result)
        rfs = {}
        tr_rfs = {}
        # other stuff
        countVar = 0
        for tr in transitions:
            if not(tr["source"] in rfvars):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["source"]] = f
                countVar += shifter
            if not(tr["target"] in rfvars):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["target"]] = f
                countVar += shifter
        if shifter == 0:
            countVar += Nvars + 1

        for tr in transitions:
            rf_s = rfvars[tr["source"]]
            rf_t = rfvars[tr["target"]]
            poly = tr["polyhedron"]
            Mcons = len(poly.get_constraints())

            # f_s >= 0
            # f_s - f_t >= 1
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons + 1
            lambdas2 = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons + 1
            farkas_constraints += farkas.LRF(poly,
                                             [lambdas, lambdas2],
                                             rf_s, rf_t)

        farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
        point = farkas_poly.get_point(use_z3=use_z3)

        if point is None:
            response.set_response(found=False,
                                  info="Farkas Polyhedron is empty.",
                                  pending_trs=transitions)
            return response

        for node in rfvars:
            rfs[node] = get_rf(rfvars[node], point)

        for tr in transitions:
            tr_rfs[tr["name"]] = {
                tr["source"]: [rfs[tr["source"]]],
                tr["target"]: [rfs[tr["target"]]]
            }

        response.set_response(found=True,
                              rfs=rfs,
                              tr_rfs=tr_rfs,
                              pending_trs=[])
        return response


class LinearRF(Manager):
    ALGORITHMS = [PR]
    ID = "lrf"

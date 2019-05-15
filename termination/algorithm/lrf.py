from termination import farkas
from termination.result import Result
from termination.result import TerminationResult
from .manager import Algorithm
from .manager import Manager
from .utils import get_rf
from .utils import get_free_name
from .utils import create_rfs


class PR(Algorithm):
    ID = "pr"
    NAME = "lrf_pr"
    DESC = "Podelski-Rybalchenko Algorithm for Linear Ranking Functions"

    def run(self, cfg, different_template=False, dt_scheme="default"):
        transitions = cfg.get_edges()
        gvs = cfg.get_info("global_vars")
        nodes = cfg.get_nodes()
        Nvars = int(len(gvs) / 2)
        response = Result()
        # farkas constraints
        farkas_constraints = []

        # 1.1 - store rfs variables
        rfvars, taken_vars = create_rfs(nodes, Nvars, 1, different_template=different_template, dt_scheme=dt_scheme)
        from lpi import Expression

        for tr in transitions:
            rf_s = rfvars[tr["source"]][0]
            rf_t = rfvars[tr["target"]][0]
            poly = tr["polyhedron"]
            Mcons = len(poly.get_constraints())

            # f_s >= 0
            # f_s - f_t >= 1
            lambdas = get_free_name(taken_vars, name="l", num=Mcons)
            taken_vars += lambdas
            lambdas2 = get_free_name(taken_vars, name="l", num=Mcons)
            taken_vars += lambdas2
            farkas_constraints += farkas.LRF(poly,
                                             [[Expression(v) for v in lambdas],
                                              [Expression(v) for v in lambdas2]],
                                             rf_s, rf_t)
        # 2 - Get Point
        from lpi import Solver
        s = Solver()
        s.add(farkas_constraints)
        point = s.get_point(taken_vars)

        if point[0] is None:
            response.set_response(status=TerminationResult.UNKNOWN,
                                  info="LRF: Farkas Polyhedron is empty.")
            return response
        rfs = {}
        for node in rfvars:
            rfs[node] = get_rf(rfvars[node][0], gvs, point)

        response.set_response(status=TerminationResult.TERMINATE, rfs=rfs)
        return response


class LinearRF(Manager):
    ALGORITHMS = [PR]
    ID = "lrf"

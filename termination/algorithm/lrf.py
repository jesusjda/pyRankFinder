from lpi import C_Polyhedron
from termination import farkas
from termination.result import Result
from termination.result import TerminationResult

from .manager import Algorithm
from .manager import Manager
from .utils import get_rf
from .utils import get_use_z3
from .utils import get_free_name


class PR(Algorithm):
    ID = "pr"
    NAME = "lrf_pr"
    DESC = "Podelski-Rybalchenko Algorithm for Linear Ranking Functions"

    def run(self, cfg, different_template=False, use_z3=None):
        transitions = cfg.get_edges()
        gvs = cfg.get_info("global_vars")
        Nvars = int(len(gvs) / 2)
        response = Result()
        use_z3 = get_use_z3(self.props, use_z3)
        # farkas Variables
        rfvars = {}
        # farkas constraints
        farkas_constraints = []
        # rfs coefficients (result)
        rfs = {}
        # other stuff
        taken_vars = []
        # 1.1 - store rfs variables
        from lpi import Expression
        if different_template:
            for tr in transitions:
                # taken_vars += tr["local_vars"]
                if not(tr["source"] in rfvars):
                    f = get_free_name(taken_vars, name="a_", num=Nvars + 1)
                    taken_vars += f
                    rfvars[tr["source"]] = [Expression(v) for v in f]
                if not(tr["target"] in rfvars):
                    f = get_free_name(taken_vars, name="a_", num=Nvars + 1)
                    taken_vars += f
                    rfvars[tr["target"]] = [Expression(v) for v in f]
        else:
            f = get_free_name(taken_vars, name="a_", num=Nvars + 1)
            taken_vars += f
            exp_f = [Expression(v) for v in f]
            for n in cfg.get_nodes():
                rfvars[n] = exp_f

        for tr in transitions:
            rf_s = rfvars[tr["source"]]
            rf_t = rfvars[tr["target"]]
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
        farkas_poly = C_Polyhedron(constraints=farkas_constraints, variables=taken_vars)

        if use_z3:
            from lpi import smtlib
            point = smtlib.get_point(farkas_poly)
        else:
            point = farkas_poly.get_point()

        if point[0] is None:
            response.set_response(status=TerminationResult.UNKNOWN,
                                  info="LRF: Farkas Polyhedron is empty.",
                                  pending_trs=transitions)
            return response
        for node in rfvars:
            rfs[node] = get_rf(rfvars[node], gvs, point)

        response.set_response(status=TerminationResult.TERMINATE,
                              rfs=rfs,
                              pending_trs=[])
        return response


class LinearRF(Manager):
    ALGORITHMS = [PR]
    ID = "lrf"

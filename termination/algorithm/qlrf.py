from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable
from termination import farkas
from termination.result import Result

from .manager import Algorithm
from .manager import Manager
from .utils import get_rf
from .utils import get_use_z3
from .utils import max_dim


class QLRF_ADFG(Algorithm):
    ID = "adfg"
    NAME = "qlrf_adfg"
    DESC = "Quasi Linear Ranking Function via QLRF_ADFG method"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, use_z3=None):
        response = Result()
        transitions = cfg.get_edges()

        dim = max_dim(transitions)
        Nvars = int(dim / 2)
        use_z3 = get_use_z3(self.props, use_z3)
        shifter = 0
        if different_template:
            shifter = Nvars + 1
        # farkas Variables
        rfvars = {}
        # farkas constraints
        farkas_constraints = []
        # return objects
        rfs = {}  # rfs coefficients (result)
        tr_rfs = {}
        no_ranked = []  # transitions sets no ranked by rfs
        # other stuff
        countVar = 0
        # 1.1 - store rfs variables
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
        countVar += Nvars + 1
        # 1.2 - store delta variables
        deltas = {transitions[i]["name"]: Variable(countVar + i)
                  for i in range(len(transitions))}
        countVar += len(transitions)
        for tr in transitions:
            rf_s = rfvars[tr["source"]]
            rf_t = rfvars[tr["target"]]
            poly = tr["polyhedron"]

            Mcons = len(poly.get_constraints())
            # f_s >= 0
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            farkas_constraints += farkas.f(poly, lambdas,
                                           rf_s, 0)

            # f_s - f_t >= delta[tr]
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            farkas_constraints += farkas.df(poly, lambdas,
                                            rf_s, rf_t, deltas[tr["name"]])
            # 0 <= delta[tr] <= 1
            farkas_constraints += [0 <= deltas[tr["name"]],
                                   deltas[tr["name"]] <= 1]

        farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
        exp = sum([deltas[tr] for tr in deltas])
        result = farkas_poly.maximize(exp)
        if not result['bounded']:
            response.set_response(found=False,
                                  info="Unbound polyhedron")
            return response
        point = result["generator"]
        zeros = True
        for c in point.coefficients():
            if c != 0:
                zeros = False
        if point is None or zeros:
            response.set_response(found=False,
                                  info="F === 0 "+str(point))
            return response

        for node in rfvars:
            rfs[node] = get_rf(rfvars[node], point)

            no_ranked = [tr for tr in transitions
                         if(point.coefficient(deltas[tr["name"]])
                            == Linear_Expression(0))]
        for tr in transitions:
            tr_rfs[tr["name"]] = {
                tr["source"]: [rfs[tr["source"]]],
                tr["target"]: [rfs[tr["target"]]]
            }

        response.set_response(found=True,
                              info="Found",
                              rfs=rfs,
                              tr_rfs=tr_rfs,
                              pending_trs=no_ranked)
        return response


class QLRF_BG(Algorithm):
    ID = "bg"
    NAME = "qlrf_bg"
    DESC = "Quasi Linear Ranking Function via QLRF_BG method"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, use_z3=None):
        response = Result()
        transitions = cfg.get_edges()

        dim = max_dim(transitions)
        Nvars = int(dim / 2)
        use_z3 = get_use_z3(self.props, use_z3)
        shifter = 0
        if different_template:
            shifter = Nvars + 1
        # farkas Variables
        rfvars = {}
        # farkas constraints
        farkas_constraints = []
        # return objects
        rfs = {}  # rfs coefficients (result)
        tr_rfs = {}
        no_ranked = []  # transitions sets no ranked by rfs
        freeConsts = []
        # other stuff
        countVar = 0
        # 1.1 - store rfs variables
        for tr in transitions:
            if not(tr["source"] in rfvars):
                if not(countVar in freeConsts):
                    freeConsts.append(countVar)
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["source"]] = f
                countVar += shifter
            if not(tr["target"] in rfvars):
                if not(countVar in freeConsts):
                    freeConsts.append(countVar)
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["target"]] = f
                countVar += shifter
        if shifter == 0:
            countVar += Nvars + 1
        size_rfs = countVar

        for tr in transitions:
            rf_s = rfvars[tr["source"]]
            rf_t = rfvars[tr["target"]]
            poly = tr["polyhedron"]
            Mcons = len(poly.get_constraints())
            # f_s >= 0
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            farkas_constraints += farkas.f(poly, lambdas,
                                           rf_s, 0)

            # f_s - f_t >= 0
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            farkas_constraints += farkas.df(poly, lambdas,
                                            rf_s, rf_t, 0)
        farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
        variables = [v for v in range(size_rfs) if not(v in freeConsts)]
        variables += freeConsts
        point = farkas_poly.get_relative_interior_point(variables)
        if point is None:
            response.set_response(found=False,
                                  info="No relative interior point")
            return response
        for node in rfvars:
            rfs[node] = get_rf(rfvars[node], point)
        # check if rfs are non-trivial
        nonTrivial = False
        dfs = {}
        for tr in transitions:
            rf_s = rfs[tr["source"]]
            rf_t = rfs[tr["target"]]
            poly = tr["polyhedron"]
            df = Linear_Expression(0)
            constant = (rf_s.coefficient(Variable(0))
                        - rf_t.coefficient(Variable(0)))
            for i in range(Nvars):
                df += Variable(i) * rf_s.coefficient(Variable(i+1))
                df -= Variable(Nvars + i) * rf_t.coefficient(Variable(i+1))
            dfs[tr["name"]] = df+constant
            if not nonTrivial:
                answ = poly.maximize(df)
                if(not answ["bounded"] or
                   answ["sup_n"] > -constant):
                    nonTrivial = True

        if nonTrivial:
            no_ranked = []
            for tr in transitions:
                poly = tr["polyhedron"]
                cons = poly.get_constraints()
                cons.insert(dfs[tr["name"]] == 0)
                newpoly = C_Polyhedron(cons)
                if not newpoly.is_empty():
                    tr["polyhedron"] = newpoly
                    no_ranked.append(tr)
                tr_rfs[tr["name"]] = {
                    tr["source"]: [rfs[tr["source"]]],
                    tr["target"]: [rfs[tr["target"]]]
                }

            response.set_response(found=True,
                                  info="found",
                                  rfs=rfs,
                                  tr_rfs=tr_rfs,
                                  pending_trs=no_ranked)
            return response
        response.set_response(found=False,
                              info="rf found was the trivial")
        return response


class QuasiLinearRF(Manager):
    ALGORITHMS = [QLRF_ADFG, QLRF_BG]
    ID = "qlrf"

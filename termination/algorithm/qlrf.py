from lpi import Expression
from termination import farkas
from termination.result import Result
from termination.result import TerminationResult

from .manager import Algorithm
from .manager import Manager
from .utils import get_rf
from .utils import get_free_name
from .utils import create_rfs


class QLRF_ADFG(Algorithm):
    ID = "adfg"
    NAME = "qlrf_adfg"
    DESC = "Quasi Linear Ranking Function via QLRF_ADFG method"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, dt_scheme="default"):
        response = Result()
        transitions = cfg.get_edges()
        nodes = cfg.get_nodes()
        gvs = cfg.get_info("global_vars")
        Nvars = int(len(gvs) / 2)
        # farkas constraints
        farkas_constraints = []
        # return objects
        no_ranked = []  # transitions sets no ranked by rfs
        # 1.1 - store rfs variables
        rfvars, taken_vars = create_rfs(nodes, Nvars, 1, different_template=different_template, dt_scheme=dt_scheme)

        # 1.2 - store delta variables
        ds = get_free_name(taken_vars, name="d", num=len(transitions))
        taken_vars += ds
        deltas = {transitions[i]["name"]: ds[i] for i in range(len(transitions))}

        for tr in transitions:
            rf_s = rfvars[tr["source"]][0]
            rf_t = rfvars[tr["target"]][0]
            poly = tr["polyhedron"]

            Mcons = len(poly.get_constraints())
            # f_s >= 0
            # f_s - f_t >= delta[tr]
            lambdas = get_free_name(taken_vars, name="l", num=Mcons)
            taken_vars += lambdas
            lambdas2 = get_free_name(taken_vars, name="l", num=Mcons)
            taken_vars += lambdas2
            farkas_constraints += farkas.LRF(poly,
                                             [[Expression(v) for v in lambdas],
                                              [Expression(v) for v in lambdas2]],
                                             rf_s, rf_t, Expression(deltas[tr["name"]]))

            # 0 <= delta[tr] <= 1
            farkas_constraints += [0 <= Expression(deltas[tr["name"]]),
                                   Expression(deltas[tr["name"]]) <= 1]

        exp = sum([Expression(deltas[tr]) for tr in deltas])

        if self.props["nonoptimal"]:
            farkas_constraints += [exp >= 1]
            from lpi import Solver
            s = Solver()
            s.add(farkas_constraints)
            point = s.get_point(taken_vars)
            if point[0] is None:
                response.set_response(status=TerminationResult.UNKNOWN,
                                      info="No point found for non-optimal adfg.")
                return response
        else:
            from lpi import C_Polyhedron
            farkas_poly = C_Polyhedron(constraints=farkas_constraints, variables=taken_vars)
            result = farkas_poly.maximize(exp)
            if not result['bounded']:
                response.set_response(status=TerminationResult.UNKNOWN,
                                      info="Unbound polyhedron")
                return response
            point = result["generator"]
        iszero = True
        for k in point[0]:
            if point[0][k] != 0:
                iszero = False
                break
        if iszero:
            response.set_response(status=TerminationResult.UNKNOWN,
                                  info="F === 0 " + str(point))
            return response

        rfs = {}
        for node in rfvars:
            rfs[node] = get_rf(rfvars[node][0], gvs, point)

            no_ranked = [tr for tr in transitions
                         if(point[0][deltas[tr["name"]]] == 0)]

        response.set_response(status=TerminationResult.TERMINATE,
                              info="Found",
                              rfs=rfs,
                              pending_trs=no_ranked)
        return response

    @classmethod
    def description(cls, long=False):
        desc = str(cls.ID) + "[_nonoptimal]"
        if long:
            desc += ": " + str(cls.DESC)
        return desc

    @classmethod
    def generate(cls, data):
        if(len(data) == 0 or
           data[0] != cls.ID):
            return None

        properties = {
            "name": data[0],
            "nonoptimal": False
        }
        data = data[1::]
        if(len(data) > 0 and
           data[0] == "nonoptimal"):
            properties["nonoptimal"] = True
            data = data[1::]
        if len(data) == 0:
            return cls(properties)
        return None


class QLRF_BG(Algorithm):
    ID = "bg"
    NAME = "qlrf_bg"
    DESC = "Quasi Linear Ranking Function via QLRF_BG method"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, dt_scheme="default"):
        response = Result()
        transitions = cfg.get_edges()
        gvs = cfg.get_info("global_vars")
        nodes = cfg.get_nodes()
        Nvars = int(len(gvs) / 2)
        # farkas constraints
        farkas_constraints = []
        # return objects
        rfs = {}  # rfs coefficients (result)
        no_ranked = []  # transitions sets no ranked by rfs
        freeConsts = []
        rf_vars = []
        # 1.1 - store rfs variables
        rfvars, taken_vars = create_rfs(nodes, Nvars, 1, different_template=different_template, dt_scheme=dt_scheme)
        for node in rfvars:
            freeConsts.append(str(rfvars[node][0][0]))
            rf_vars += [str(v) for v in rfvars[node][0][1:]]

        freeConsts = list(set(freeConsts))
        rf_vars = list(set(rf_vars))

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
                                             rf_s, rf_t, 0)
        from lpi import C_Polyhedron
        farkas_poly = C_Polyhedron(constraints=farkas_constraints, variables=taken_vars)

        variables = rf_vars + freeConsts
        point = farkas_poly.get_relative_interior_point(variables)
        if point[0] is None:
            response.set_response(status=TerminationResult.UNKNOWN,
                                  info="No relative interior point")
            return response

        for node in rfvars:
            rfs[node] = get_rf(rfvars[node][0], gvs, point)

        # check if rfs are non-trivial
        nonTrivial = False
        dfs = {}
        for tr in transitions:
            rf_s = rfs[tr["source"]]
            rf_t = rfs[tr["target"]].renamed(gvs[:Nvars], gvs[Nvars:])
            poly = tr["polyhedron"]
            df = rf_s - rf_t  # ExprTerm(0)
            constant = (rf_s.get_coeff() - rf_t.get_coeff())
            # for i in range(Nvars):
            #     df += gvs[i] * rf_s.coefficient(Variable(i + 1))
            #     df -= gvs[Nvars + i] * rf_t.coefficient(Variable(i + 1))
            dfs[tr["name"]] = df  # + constant
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
                cons.append(dfs[tr["name"]] == 0)
                newpoly = C_Polyhedron(constraints=cons, variables=gvs+tr["local_vars"])
                if not newpoly.is_empty():
                    tr["polyhedron"] = newpoly
                    no_ranked.append(tr)

            response.set_response(status=TerminationResult.TERMINATE,
                                  info="found",
                                  rfs=rfs,
                                  pending_trs=no_ranked)
            return response
        response.set_response(status=TerminationResult.UNKNOWN,
                              info="rf found was the trivial")
        return response


class QLRF_BMS(Algorithm):
    ID = "bms"
    NAME = "qlrf_bms"
    DESC = "Quasi Linear Ranking Function via QLRF_BMS method"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, dt_scheme="default"):
        response = Result()
        transitions = cfg.get_edges()
        gvs = cfg.get_info("global_vars")
        nodes = cfg.get_nodes()
        Nvars = int(len(gvs) / 2)
        # farkas constraints
        farkas_constraints = []
        # return objects
        rfs = {}  # rfs coefficients (result)
        no_ranked = []  # transitions sets no ranked by rfs
        freeConsts = []
        rf_vars = []
        # 1.1 - store rfs variables
        rfvars, taken_vars = create_rfs(nodes, Nvars, 1, different_template=different_template, dt_scheme=dt_scheme)
        for tr in transitions:
            rf_s = rfvars[tr["source"]][0]
            rf_t = rfvars[tr["target"]][0]
            poly = tr["polyhedron"]
            Mcons = len(poly.get_constraints())
            # f_s - f_t >= 0
            lambdas = get_free_name(taken_vars, name="l", num=Mcons)
            taken_vars += lambdas
            farkas_constraints += farkas.df(poly,[Expression(v) for v in lambdas],
                                            rf_s, rf_t, 0)
        from lpi import Solver
        for i in range(len(transitions)):
            tr = transitions[i]
            act_taken_vars = []+taken_vars
            rf_s = rfvars[tr["source"]][0]
            rf_t = rfvars[tr["target"]][0]
            poly = tr["polyhedron"]
            Mcons = len(poly.get_constraints())
            # f_s >= 0
            # f_s - f_t >= 1
            lambdas = get_free_name(act_taken_vars, name="L", num=Mcons)
            act_taken_vars += lambdas
            lambdas2 = get_free_name(act_taken_vars, name="L", num=Mcons)
            act_taken_vars += lambdas2
            local_farkas_constraints = farkas.LRF(poly, 
                                                  [[Expression(v) for v in lambdas],
                                                   [Expression(v) for v in lambdas2]],
                                                  rf_s, rf_t, 1)
            s = Solver()
            s.add(farkas_constraints+local_farkas_constraints)
            point = s.get_point(act_taken_vars)
            if point[0] is None:
                continue
            iszero = True
            for k in point[0]:
                if point[0][k] != 0:
                    iszero = False
                    break
            if iszero:
                continue
            for node in rfvars:
                rfs[node] = get_rf(rfvars[node][0], gvs, point)

                response.set_response(status=TerminationResult.TERMINATE,
                                      info="found",
                                      rfs=rfs,
                                      pending_trs=transitions[:i]+transitions[i+1:])
                return response
        response.set_response(status=TerminationResult.UNKNOWN,
                              info="Not found .")
        return response

class QuasiLinearRF(Manager):
    ALGORITHMS = [QLRF_ADFG, QLRF_BG, QLRF_BMS]
    ID = "qlrf"

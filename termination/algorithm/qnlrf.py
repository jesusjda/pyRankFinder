from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Variable
from termination import farkas
from termination.output import Output_Manager as OM
from termination.result import Result
from termination.result import TerminationResult
from .manager import Algorithm
from .manager import Manager
from .utils import get_rf
from .utils import get_use_z3
from .utils import max_dim


class QNLRF(Algorithm):
    ID = "qnlrf"
    NAME = "qnlrf"
    DESC = "Quasi Nested Linear Ranking Function"

    def __init__(self, properties={}):
        self.props = properties

    @classmethod
    def description(cls, long=False):
        desc = str(cls.ID) + "[_v2][_N]"
        if long:
            desc += ": " + str(cls.DESC)
        return desc

    def run(self, cfg, different_template=False, use_z3=None):
        response = Result()
        all_transitions = cfg.get_edges()
        use_z3 = get_use_z3(self.props, use_z3)
        max_d = self.props["max_depth"] + 1
        min_d = self.props["min_depth"]
        version = self.props["version"]
        dim = max_dim(all_transitions)
        Nvars = int(dim / 2)

        for tr_idx in range(len(all_transitions)):
            main_tr = all_transitions[tr_idx]
            transitions = [all_transitions[j]
                           for j in range(len(all_transitions))
                           if j != tr_idx]
            OM.printif(2, "trying with : " + main_tr["name"])
            for d in range(min_d, max_d):
                OM.printif(2, "\td = ", d)
                # 0 - create variables
                shifter = 0
                if different_template:
                    shifter = (Nvars + 1) * (d)
                # 0.1 - farkas Variables
                rfvars = {}
                # 0.2 - farkas constraints
                farkas_constraints = []
                # 0.3 - return objects
                rfs = {}  # rfs coefficients (result)
                # 0.4 - other stuff
                countVar = 0

                # 1 - init variables
                # 1.1 - store rfs variables
                for tr in all_transitions:
                    if not(tr["source"] in rfvars):
                        f = [[Variable(i)
                              for i in range(countVar + (Nvars + 1) * di,
                                             countVar + (Nvars + 1) * (di + 1))]
                             for di in range(d)]
                        rfvars[tr["source"]] = f
                        countVar += shifter
                    if not(tr["target"] in rfvars):
                        f = [[Variable(i)
                              for i in range(countVar + (Nvars + 1) * di,
                                             countVar + (Nvars + 1) * (di + 1))]
                             for di in range(d)]
                        rfvars[tr["target"]] = f
                        countVar += shifter
                if shifter == 0:
                    countVar += (Nvars + 1) * d
                # 1.2 - calculate farkas constraints
                rf_s = rfvars[main_tr["source"]]
                rf_t = rfvars[main_tr["target"]]
                poly = main_tr["polyhedron"]
                Mcons = len(poly.get_constraints())

                lambdas = [[Variable(countVar + k + Mcons * di)
                            for k in range(Mcons)]
                           for di in range(d + 1)]
                countVar += Mcons * (d + 1)
                # 1.2.3 - NLRF for tr
                farkas_constraints += farkas.NLRF(poly, lambdas,
                                                  rf_s, rf_t)
                # 1.2.4 - df >= 0 for each tri != tr

                for tr2 in transitions:
                    Mcons2 = len(tr2["polyhedron"].get_constraints())
                    rf_s2 = rfvars[tr2["source"]]
                    rf_t2 = rfvars[tr2["target"]]
                    if version == 2:
                        lambdas = [[Variable(countVar + k + Mcons2 * di)
                                    for k in range(Mcons2)]
                                   for di in range(d)]
                        countVar += Mcons2 * d
                        farkas_constraints += farkas.QNLRF(tr2["polyhedron"],
                                                           lambdas, rf_s2,
                                                           rf_t2, 0)
                    else:
                        for di in range(d):
                            lambdas = [Variable(countVar + k)
                                       for k in range(Mcons2)]
                            farkas_constraints += farkas.df(tr2["polyhedron"],
                                                            lambdas, rf_s2[di],
                                                            rf_t2[di], 0)
                            countVar += Mcons2

                # 2 - Polyhedron
                farkas_poly = C_Polyhedron(
                    Constraint_System(farkas_constraints))
                point = farkas_poly.get_point(use_z3=use_z3)
                if point is None:
                    continue  # not found, try with next d

                for node in rfvars:
                    rfs[node] = [get_rf(rfvars[node][di], point)
                                 for di in range(d)]

                response.set_response(status=TerminationResult.TERMINATE,
                                      info="found",
                                      rfs=rfs,
                                      pending_trs=transitions)
                return response

        response.set_response(status=TerminationResult.UNKNOWN,
                              info="Not found: max_d = " + str(max_d - 1) + " .",
                              pending_trs=transitions)
        return response

    @classmethod
    def generate(cls, data):
        if(len(data) == 0 or
           data[0] != cls.ID):
            return None

        properties = {
            "name": data[0],
            "version": 1,
            "max_depth": 5,
            "min_depth": 1
        }
        data = data[1::]
        if(len(data) > 0 and
           data[0] == "v2"):
            properties["version"] = 2
            data = data[1::]
        if len(data) > 0:
            try:
                properties["max_depth"] = int(data[0])
                data = data[1::]
            except ValueError:
                return None
        if len(data) > 0:
            try:
                properties["min_depth"] = properties["max_depth"]
                properties["max_depth"] = int(data[0])
                data = data[1::]
            except ValueError:
                return None
        if len(data) == 0:
            return cls(properties)
        return None


class QuasiNestedLRF(Manager):
    ALGORITHMS = [QNLRF]
    ID = "qnlrf"

    @classmethod
    def get_algorithm(cls, token):
        if isinstance(token, str):
            data = token.split("_")
        else:
            data = token
        if data[0] == cls.ID:
            for opt in cls.ALGORITHMS:
                alg = opt.generate(data)
                if alg is None:
                    continue
                return alg
        raise ValueError("Not Valid token")

    @classmethod
    def options(cls, long=False):
        return [opt.description(long=long)
                for opt in cls.ALGORITHMS]

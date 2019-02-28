from lpi import C_Polyhedron
from termination import farkas
from termination.output import Output_Manager as OM
from termination.result import Result
from termination.result import TerminationResult
from .manager import Algorithm
from .manager import Manager
from .utils import get_rf
from .utils import get_free_name


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

    def run(self, cfg, different_template=False):
        response = Result()
        all_transitions = cfg.get_edges()
        gvs = cfg.get_info("global_vars")
        Nvars = int(len(gvs) / 2)
        max_d = self.props["max_depth"] + 1
        min_d = self.props["min_depth"]
        version = self.props["version"]

        for tr_idx in range(len(all_transitions)):
            main_tr = all_transitions[tr_idx]
            transitions = all_transitions[:tr_idx] + all_transitions[tr_idx + 1:]

            OM.printif(2, "trying with : " + main_tr["name"])
            for d in range(min_d, max_d):
                OM.printif(2, "\td = ", d)
                # 0 - create variables
                # 0.1 - farkas Variables
                rfvars = {}
                # 0.2 - farkas constraints
                farkas_constraints = []
                # 0.3 - return objects
                rfs = {}  # rfs coefficients (result)
                # 0.4 - other stuff
                taken_vars = []

                # 1 - init variables
                # 1.1 - store rfs variables
                from lpi import Expression
                if different_template:
                    for tr in all_transitions:
                        if tr["source"] not in rfvars:
                            f = []
                            for di in range(d):
                                name = "a_" + str(di) + "_"
                                fi = get_free_name(taken_vars, name=name, num=Nvars + 1)
                                f.append(fi)
                                taken_vars += fi
                            rfvars[tr["source"]] = [[Expression(v) for v in fi] for fi in f]
                        if tr["target"] not in rfvars:
                            f = []
                            for di in range(d):
                                name = "a_" + str(di) + "_"
                                fi = get_free_name(taken_vars, name=name, num=Nvars + 1)
                                f.append(fi)
                                taken_vars += fi
                            rfvars[tr["target"]] = [[Expression(v) for v in fi] for fi in f]
                else:
                    f = []
                    for di in range(d):
                        name = "a_" + str(di) + "_"
                        fi = get_free_name(taken_vars, name=name, num=Nvars + 1)
                        f.append(fi)
                        taken_vars += fi
                    exp_f = [[Expression(v) for v in fi] for fi in f]
                    for n in cfg.get_nodes():
                        rfvars[n] = exp_f

                # 1.2 - calculate farkas constraints
                rf_s = rfvars[main_tr["source"]]
                rf_t = rfvars[main_tr["target"]]
                poly = main_tr["polyhedron"]
                Mcons = len(poly.get_constraints())

                lambdas = []
                for di in range(d + 1):
                    name = "l_" + str(di) + "_"
                    li = get_free_name(taken_vars, name=name, num=Mcons)
                    lambdas.append([Expression(l) for l in li])
                    taken_vars += li

                # 1.2.3 - NLRF for tr
                farkas_constraints += farkas.NLRF(poly, lambdas,
                                                  rf_s, rf_t)
                # 1.2.4 - for each tri != tr

                for tr2 in transitions:
                    Mcons2 = len(tr2["polyhedron"].get_constraints())
                    rf_s2 = rfvars[tr2["source"]]
                    rf_t2 = rfvars[tr2["target"]]
                    if version == 2:
                        # fs[0] - ft[0] >= 0
                        # (fs[i] - ft[i]) + fs[i-1] >= 0
                        lambdas = []
                        for di in range(d):
                            name = "l2_" + str(di) + "_"
                            li = get_free_name(taken_vars, name=name, num=Mcons2)
                            lambdas.append([Expression(l) for l in li])
                            taken_vars += li

                        farkas_constraints += farkas.QNLRF(tr2["polyhedron"],
                                                           lambdas, rf_s2,
                                                           rf_t2, 0)
                    else:  # fs[i] - ft[i] >= 0 for each i=0...(d-1)
                        for di in range(d):
                            lambdas = get_free_name(taken_vars, name="l", num=Mcons2)
                            taken_vars += lambdas
                            farkas_constraints += farkas.df(tr2["polyhedron"],
                                                            [Expression(l) for l in lambdas],
                                                            rf_s2[di], rf_t2[di], 0)

                # 2 - Get Point
                from lpi import Solver
                s = Solver()
                s.add(farkas_constraints)
                point = s.get_point(taken_vars)

                if point[0] is None:
                    continue  # not found, try with next d

                for node in rfvars:
                    rfs[node] = [get_rf(rfvars[node][di], gvs, point)
                                 for di in range(d)]

                response.set_response(status=TerminationResult.TERMINATE,
                                      info="found",
                                      rfs=rfs,
                                      pending_trs=transitions)
                return response

        response.set_response(status=TerminationResult.UNKNOWN,
                              info="Not found: max_d = " + str(max_d - 1) + " .")
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

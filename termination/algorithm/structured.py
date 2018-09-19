from termination.result import Result
from termination.result import TerminationResult
from .manager import Algorithm

from .manager import Manager


class Lex(Algorithm):
    ID = "lex"
    NAME = "Lex"
    DESC = "Lexicographic Ranking Function"

    def __init__(self, properties={}):
        self.props = properties

    @classmethod
    def generate(cls, data):
        if(len(data) == 0 or
           data[0] != cls.ID):
            return None
        if data[0] == cls.ID:
            from . import Termination_Algorithm_Manager as AM
            properties = {}
            properties["inner_alg"] = AM.get_algorithm(data[1::])
            return cls(properties)
        return None

    @classmethod
    def description(cls, long=False):
        desc = str(cls.ID) + "_ALGORITHM"
        if long:
            desc += ": " + str(cls.DESC)
        return desc

    def run(self, cfg, different_template=False, use_z3=None):
        response = Result()
        transitions = cfg.get_edges()

        rfs = {}
        no_ranked_trs = transitions
        i = 0
        inner_alg = self.props["inner_alg"]

        while no_ranked_trs:  # while not empty
            i += 1
            trs = [tr.copy() for tr in no_ranked_trs]
            inner_cfg = cfg.edge_data_subgraph(trs)
            result = inner_alg.run(inner_cfg,
                                   different_template=different_template,
                                   use_z3=use_z3)
            if result.error():
                return result
            elif not result.get_status().is_terminate():
                response.set_response(status=TerminationResult.UNKNOWN,
                                      info=result.get("info"),
                                      rfs=rfs,
                                      pending_trs=no_ranked_trs)
                return response
            else:
                pending_trs = result.get("pending_trs")
                if False and len(no_ranked_trs) <= len(pending_trs):
                    response.set_response(status=TerminationResult.UNKNOWN,
                                          info="No decreasing",
                                          rfs=rfs,
                                          pending_trs=no_ranked_trs)
                    return response
                res_rfs = result.get("rfs")
                for node in res_rfs:
                    if not(node in rfs):
                        rfs[node] = []
                    rfs[node].append(res_rfs[node])
                no_ranked_trs = pending_trs

        response.set_response(status=TerminationResult.TERMINATE,
                              rfs=rfs,
                              pending_trs=[])
        return response


class BMS(Algorithm):
    ID = "bms"
    NAME = "BMS"
    DESC = "Bradley-Manna-Sipma Ranking Function algorithm over lrf_pr or qnlrf"

    def __init__(self, properties={}):
        self.props = properties

    @classmethod
    def generate(cls, data):
        if(len(data) == 0 or
           data[0] != cls.ID):
            return None
        if data[0] == cls.ID:
            from . import Termination_Algorithm_Manager as AM
            properties = {}
            properties["inner_alg"] = AM.get_algorithm(data[1::])
            return cls(properties)
        return None

    @classmethod
    def description(cls, long=False):
        desc = str(cls.ID) + "_lrf_pr or " + str(cls.ID) + "_qnlrf[*]"
        if long:
            desc += ": " + str(cls.DESC)
        return desc

    def run(self, cfg, different_template=False, use_z3=None):
        response = Result()

        rfs = {}
        inner_alg = self.props["inner_alg"]

        result = inner_alg.run(cfg, different_template=different_template,
                               use_z3=use_z3)  # Run NLRF or LRF

        if result.get_status().is_terminate():
            trfs = result.get("rfs")
            for key in trfs:
                if not(key in rfs):
                    rfs[key] = []
                rfs[key].append(trfs[key])

            no_ranked_trs = result.get("pending_trs")
            trs = [tr.copy() for tr in no_ranked_trs]

            if len(trs) > 0:
                inner_cfg = cfg.edge_data_subgraph(trs)
                # Run BMS
                bmsresult = self.run(inner_cfg,
                                     different_template=different_template)
                if bmsresult.get_status().is_terminate():
                    bms_rfs = bmsresult.get("rfs")
                    # merge rfs
                    for key in bms_rfs:
                        if not(key in rfs):
                            rfs[key] = []
                        rfs[key].append(bms_rfs[key])
                    response.set_response(status=TerminationResult.TERMINATE,
                                          info="Found",
                                          rfs=rfs,
                                          pending_trs=[],
                                          tr_rfs={})

                    return response
                else:
                    return bmsresult
            else:
                response.set_response(status=TerminationResult.TERMINATE,
                                      info="Found",
                                      rfs=rfs,
                                      pending_trs=[])
                return result

        # Impossible to find a BMS
        response.set_response(status=TerminationResult.UNKNOWN,
                              info="No BMS",
                              rfs=rfs,
                              pending_trs=result.get("pending_trs"))
        return response


class Structured(Manager):
    ALGORITHMS = [Lex, BMS]
    ID = ""

    @classmethod
    def get_algorithm(cls, token):
        if isinstance(token, str):
            data = token.split("_")
        else:
            data = token
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

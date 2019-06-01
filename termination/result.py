from lpi import Expression
try:
    from enum import Enum
except ImportError:
    class Enum(set):
        def __getattr__(self, name):
            if name in self:
                return name
            raise AttributeError
from .output import Output_Manager as OM

__all__ = ["TerminationResult", "Result"]


class TerminationResult(Enum):
    TERMINATE = "Terminate"
    NONTERMINATE = "Non-Terminate"
    UNKNOWN = "Unknown"
    ERROR = "Error"
    TIMELIMIT = "Time Limit"
    MEMORYLIMIT = "Memory Limit"

    def is_terminate(self):
        return self == TerminationResult.TERMINATE

    def is_nonterminate(self):
        return self == TerminationResult.NONTERMINATE

    def is_error(self):
        return self == TerminationResult.ERROR

    def __str__(self):
        return "{}".format(self.value)

    def __repr__(self):
        return self.__str__()


class Result:

    _data = {}

    def __init__(self, status=TerminationResult.UNKNOWN, errormsg="", **kwargs):
        self._data = kwargs
        self._data["status"] = status
        self._data["errormsg"] = errormsg
        if not ("info" in self._data):
            self._data["info"] = ""

    def get_status(self):
        return self._data["status"]

    def get(self, key):
        return self._data[key]

    def has(self, key):
        return key in self._data

    def set_error(self, errormsg):
        self._data["errormsg"] = errormsg
        self._data["status"] = TerminationResult.ERROR

    def set_response(self, **kwargs):
        self._data.update(kwargs)

    def _rfs2str(self, rfs, vars_name=None):
        res = ""
        if isinstance(rfs, list):
            res += "[\n"
            for i in range(len(rfs)):
                res += self._rfs2str(rfs[i], vars_name)
            res += "]"
        else:
            for node in sorted(rfs.keys()):
                res += node + ": " + self._rflist2str(rfs[node], vars_name)
                res += "\n"
        return res

    def _rflist2str(self, rfs, vars_name=None):
        res = ""
        if isinstance(rfs, Expression):
            res += OM.tostr(rfs, vars_name)
        else:
            res += "< "
            for i in range(len(rfs)):
                if i != 0:
                    res += ", "
                res += self._rflist2str(rfs[i], vars_name)
            res += " >"
        return res

    def _function2str(self, rf, vars_name=None):
        coeffs = rf[0]
        inh = rf[1]
        sr = ""
        if vars_name is None:
            vars_name = ["x" + str(i) for i in range(len(coeffs))]
        for i in range(len(coeffs)):
            if coeffs[i] == 0:
                continue
            if coeffs[i] == 1:
                sr += str(vars_name[i]) + " + "
                continue
            sr = (sr + "" + str(coeffs[i]) + " * " +
                  str(vars_name[i]) + " + ")
        sr += "" + str(inh)
        return sr

    def toString(self, vars_name=None):
        res_str = "MAYBE\n"
        if self.get_status().is_terminate():
            res_str = "YES\n"
        if self.get_status().is_nonterminate():
            res_str = "NO\n"
        if self._data["status"].is_error():
            return res_str + "\nERROR: " + self._data["errormsg"]
        if "info" in self._data:
            res_str += "\n" + str(self._data["info"])
        if "rfs" in self._data:
            res_str += self._rfs(self._data["rfs"], vars_name)
        if "nonterminate" in self._data:
            res_str += self._scc_nonterminate(self._data["nonterminate"], vars_name)
        if "unknown_sccs" in self._data:
            res_str += self._unknown_sccs(self._data["unknown_sccs"])
        return res_str

    def _rfs(self, rfs, vars_name=None):
        if len(rfs) == 0:
            return ""
        res_str = "\nTermination: (Ranking Functions Found)\n"
        res_str += "------------\n"
        return res_str + self._rfs2str(rfs, vars_name) + "\n"

    def toStrRankingFunctions(self, vars_name=None):
        rfs = self._data["rfs"] if self.has("rfs") else []
        if len(rfs) == 0:
            return ""
        return self._rfs2str(rfs, vars_name)

    def _scc_nonterminate(self, sols_nt, vars_name):
        if len(sols_nt) == 0:
            return ""
        res_str = "\nNON-Termination: (Didn't check reachability)\n"
        res_str += "----------------\n"
        for sol in sols_nt:
            scc = sol.get("graph")
            ns = scc.get_nodes()
            ts = scc.get_edges()
            res_str += "SCC:\n+--transitions: {}\n+--nodes: {}\n".format(
                ",".join([t["name"] for t in ts]), ",".join(ns))
            if sol.has("close_walk"):
                res_str += "Closed walk: " + str(len(sol.get("close_walk"))) + " -> " + ", ".join([t["name"]for t in sol.get("close_walk")])
            if sol.has("info"):
                res_str += "\n- " + sol.get("info") + "\n"
            if sol.has("fixpoint"):
                res_str += "-> {"
                fx = sol.get("fixpoint")
                res_str += ", ".join(["{}: {}".format(v, fx[v]) for v in fx])
                res_str += "}\n"
            if sol.has("rec_set"):
                res_str += str(sol.get("rec_set"))
        return res_str

    def _unknown_sccs(self, unk_sccs):
        if len(unk_sccs) == 0:
            return ""
        res_str = "\nConnected Subgraphs where we couldn't prove Termination:\n"
        res_str += "--------------------------------------------------------\n"
        for scc in unk_sccs:
            ns = scc.get_nodes()
            ts = scc.get_edges()
            res_str += "SCC:\n+--transitions: {}\n+--nodes: {}\n".format(
                ",".join([t["name"] for t in ts]), ",".join(ns))

        return res_str + "\n"

    def __repr__(self):
        return self.toString()

    def debug(self):
        return self._data

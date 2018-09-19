try:
    from enum import Enum
except ImportError:
    class Enum(set):
        def __getattr__(self, name):
            if name in self:
                return name
            raise AttributeError
from ppl import Generator
from .output import Output_Manager as OM

class TerminationResult(Enum):
    TERMINATE = "Terminate"
    NONTERMINATE = "Non-Terminate"
    UNKNOWN = "Unknown"
    ERROR = "Error"
    TIMELIMIT = "Time Limit"
    MEMORYLIMIT = "Memory Limit"

    def is_terminate(self):
        return self == TerminationResult.TERMINATE

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
            for node in rfs:
                res += node + ": " + self._rflist2str(rfs[node], vars_name)
                res += "\n"
        return res

    def _rflist2str(self, rfs, vars_name=None):
        res = ""
        if isinstance(rfs, Generator):
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

    def toString(self, vars_name=None, ei=False):
        if self._data["status"].is_error():
            return "ERROR: " + self._data["errormsg"]
        if not self._data["status"].is_terminate():
            return "NOT FOUND " + self._data["info"]

        res = "FOUND"
        if "type" in self._data:
            res += " (" + self._data["type"] + ")"
        res += ":\n"
        if "rfs" in self._data:
            res += self._rfs2str(self._data["rfs"], vars_name)
        else:
            res += self._data
        return res

    def __repr__(self):
        return self.toString()

    def debug(self):
        return self._data

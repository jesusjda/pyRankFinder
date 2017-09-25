import termination.algorithm


def run(data):
    config = data.copy()
    alg = config["algorithm"]
    if alg == "lex":
        return algorithm.LexicographicRF(config)
    elif alg == "bms":
        return algorithm.BMSRF(config)
    elif alg == "prlrf":
        return algorithm.LinearRF(config)
    elif alg == "adfglrf":
        return algorithm.compute_adfg_QLRF(config)
    elif alg == "bgllrf":
        return algorithm.compute_bg_QLRF(config)
    elif alg == "bmslrf":
        return algorithm.compute_bms_LRF(config)
    elif alg == "bmsnlrf":
        return algorithm.compute_bms_NLRF(config)
    else:
        raise Exception("ERROR: Algorithm (" + alg + ") not found.")


class Result:

    _data = {}

    def __init__(self, found=False, error=False, errormsg="", **kwargs):
        self._data = kwargs
        self._data["found"] = found
        self._data["error"] = error
        self._data["errormsg"] = errormsg

    def found(self):
        return not self._data["error"] and self._data["found"]

    def error(self):
        return self._data["error"]

    def get(self, key):
        return self._data[key]

    def has(self, key):
        return key in self._data

    def set_error(self, errormsg):
        self._data["errormsg"] = errormsg
        self._data["error"] = True

    def set_response(self, **kwargs):
        self._data.update(kwargs)

    def _rfs2str(self, rfs, vars_name=None):
        res = ""
        for node in rfs:
            res += node + ": " + self._rflist2str(rfs[node], vars_name)
            res += "\n"
        return res

    def _rflist2str(self, rfs, vars_name=None):
        res = ""
        if isinstance(rfs, tuple):
            res += self._function2str(rfs, vars_name)
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
            vars_name = ["x"+str(i) for i in range(len(coeffs))]
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
        if self._data["error"]:
            return "ERROR: " + self._data["errormsg"]

        if not self._data["found"]:
            return "NOT FOUND: " + self._data["info"]

        res = "FOUND"
        if "type" in self._data:
            res += " (" + self._data["type"] + ")"
        res += ": "
        if "rfs" in self._data:
            res += self._rfs2str(self._data["rfs"])
        else:
            res += self._data
        return res

    def __repr__(self):
        return self.toString()

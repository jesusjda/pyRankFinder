import terminationalgorithm


def run(config):
    new_config = config.copy()

    if "transitions" in config:
        new_config["transitions"] = config["transitions"]
        new_config["vars_name"] = config["vars_name"]
    else:
        new_config["transitions"] = config["cfg"].get_edges()
        new_config["vars_name"] = config["cfg"].get_var_name()

    return _runalgorithm(new_config)


def apply_strategy(strategy, transitions):
    if strategy == "global":
        return transitions
    elif strategy == "local":
        raise NotImplementedError
    elif strategy == "incremental":
        raise NotImplementedError
    else:
        raise Exception("SCC unknown")


def _runalgorithm(config):
    alg = config["algorithm"]
    if alg == "lex":
        return terminationalgorithm.LexicographicRF(config)
    elif alg == "bms":
        return terminationalgorithm.BMSRF(config)
    elif alg == "prlrf":
        return terminationalgorithm.LinearRF(config)
    elif alg == "adfglrf":
        return terminationalgorithm.compute_adfg_QLRF(config)
    elif alg == "bgllrf":
        return terminationalgorithm.compute_bg_QLRF(config)
    elif alg == "bmslrf":
        return terminationalgorithm.compute_bms_LRF(config)
    elif alg == "bmsnlrf":
        return terminationalgorithm.compute_bms_NLRF(config)
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

    def set_error(self, errormsg):
        self._data["errormsg"] = errormsg
        self._data["error"] = True

    def set_response(self, **kwargs):
        self._data.update(kwargs)

    def _rfs2str(self, rfs):
        res = ""
        for node in rfs:
            res += node + ": " + self._rflist2str(rfs[node])
            res += "\n"
        return res

    def _rflist2str(self, rfs):
        res = ""
        if isinstance(rfs, tuple):
            res += self._function2str(rfs)
        else:
            res += "< "
            for i in range(len(rfs)):
                if i != 0:
                    res += ", "
                res += self._rflist2str(rfs[i])
            res += " >"
        return res

    def _function2str(self, rf):
        coeffs = rf[0]
        inh = rf[1]
        sr = ""
        for i in range(len(coeffs)):
            if coeffs[i] == 0:
                continue
            if coeffs[i] == 1:
                sr += str(self._data["vars_name"][i]) + " + "
                continue
            sr = (sr + "" + str(coeffs[i]) + " * " +
                  str(self._data["vars_name"][i]) + " + ")
        sr += "" + str(inh)
        return sr

    def __repr__(self):
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

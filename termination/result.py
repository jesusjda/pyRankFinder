class Result:

    _data = {}

    def __init__(self, found=False, error=False, errormsg="", **kwargs):
        self._data = kwargs
        self._data["found"] = found
        self._data["error"] = error
        self._data["errormsg"] = errormsg
        if not ("info" in self._data):
            self._data["info"] = ""

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

    def _trrfs2str(self, tr_rfs, vars_name=None):
        return "NOT IMPLEMENTED YET"

    def toString(self, vars_name=None, ei=False):
        if self._data["error"]:
            return "ERROR: " + self._data["errormsg"]

        if not self._data["found"]:
            return "NOT FOUND: " + self._data["info"]

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

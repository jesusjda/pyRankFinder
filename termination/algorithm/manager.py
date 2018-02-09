class Algorithm(object):

    def run(self, cfg, different_template=False, use_z3=None):
        raise NotImplementedError()

    @classmethod
    def generate(cls, data):
        if len(data) != 1:
            return None
        if data[0] == cls.ID:
            try:
                c = cls()
            except Exception as e:
                raise Exception() from e
            return c
        return None

    @classmethod
    def description(cls, long=False):
        desc = str(cls.ID)
        if long:
            desc += ": " + str(cls.DESC)
        return desc

    def __repr__(self):
        cad_alg = self.NAME
        if "version" in self.props:
            cad_alg += " version: " + str(self.props["version"])
        return cad_alg


class Manager:

    @classmethod
    def get_algorithm(cls, token):
        if isinstance(token, str):
            data = token.split("_")
        else:
            data = token
        if data[0] == cls.ID:
            for opt in cls.ALGORITHMS:
                alg = opt.generate(data[1::])
                if alg is None:
                    continue
                return alg
        raise ValueError("Not Valid token")

    @classmethod
    def options(cls, long=False):
        return [cls.ID + "_" + opt.description(long=long)
                for opt in cls.ALGORITHMS]

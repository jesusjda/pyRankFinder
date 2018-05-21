from termination.profiler import register_as


class Algorithm(object):

    def __init__(self, properties={}):
        self.props = properties

    @register_as("runalgorithm")
    def run(self, cfg, different_template=False, use_z3=None):
        raise NotImplementedError()

    @classmethod
    def generate(cls, data):
        if len(data) != 1:
            return None
        if data[0] == cls.ID:
            try:
                c = cls()
            except Exception:
                raise 
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

    def set_prop(self, key, value):
        self.props[key] = value

    def get_prop(self, key):
        return self.props[key]

    def has_prop(self, key):
        return key in self.props


class Manager:
    
    @classmethod
    @register_as("getalgorithm")
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

from termination.algorithm.factory import Algorithm

from .factory import Manager
from .lrf import LinearRF
from termination.algorithm.structured import Structured
from .qlrf import QuasiLinearRF
from .qnlrf import QuasiNestedLRF


__all__ = ["Algorithm_Manager"]


class Algorithm_Manager(Manager):
    ALGORITHMS = [LinearRF, QuasiLinearRF, QuasiNestedLRF, Structured]
    ID = ""

    @classmethod
    def get_algorithm(cls, token):
        if isinstance(token, str):
            data = token.split("_")
        else:
            data = token
        for opt in cls.ALGORITHMS:
            try:
                alg = opt.get_algorithm(data)
                if alg is None:
                    continue
                return alg
            except ValueError:
                continue
        raise ValueError("Not Valid Token")

    @classmethod
    def options(cls, long=False):
        opts = []
        for o in cls.ALGORITHMS:
            opts += o.options(long=long)
        return opts

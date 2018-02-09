from .lrf import LinearRF
from .manager import Algorithm
from .manager import Manager
from .qlrf import QuasiLinearRF
from .qnlrf import QuasiNestedLRF
from .structured import Structured


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

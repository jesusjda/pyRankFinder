from copy import deepcopy

__all__ = ["PolyhedraAbstractState", "IntervalAbstractState", "state"]

class AbstractState(object):

    def __init__(self, arg1, bottom=False):
        raise Exception("Abstract State")

    def _assert_same_type(self, s):
        if not(type(self) is type(s)):
            raise TypeError("Not same type of State")

    def copy(self, copy=True):
        if copy:
            return deepcopy(self)
        else:
            return self

    def lub(self, s2, copy=False):
        pass

    def widening(self, s2, threshold=None, copy=False):
        if threshold is not None:
            self.extrapolation_assign(s2, threshold, copy)
        else:
            self.widening_assign(s2, copy)

    def apply_tr(self, tr, copy=False):
        pass

    def get_constraints(self):
        pass

    def __le__(self, s2):
        pass

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def __repr__(self):
        return "{{{}}}".format(", ".join(self.toString()))

from .polyhedra import PolyhedraAbstractState
from .interval import IntervalAbstractState


def state(n, bottom=False, abstract_domain="polyhedra"):
    if abstract_domain.lower() == "polyhedra":
        return PolyhedraAbstractState(n, bottom=bottom)
    elif abstract_domain.lower() == "interval":
        return IntervalAbstractState(n, bottom=bottom)
    else:
        raise NotImplementedError("{} state type is NOT implemented.".format(abstract_domain))

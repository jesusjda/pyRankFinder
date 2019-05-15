__all__ = ["PolyhedraAbstractState", "IntervalAbstractState", "state"]


class AbstractState(object):

    def __init__(self, arg1, bottom=False):
        raise Exception("Abstract State")

    def _assert_same_type(self, s):
        if not(type(self) is type(s)):
            raise TypeError("Not same type of State")

    def copy(self, copy=True): raise NotImplementedError()

    def lub(self, s2, copy=False): raise NotImplementedError()

    def widening(self, s2, threshold=None, copy=False):
        if threshold is not None:
            self.extrapolation_assign(s2, threshold, copy)
        else:
            self.widening_assign(s2, copy)

    def widening_assign(self, s2, copy=False): raise NotImplementedError()

    def extrapolation_assign(self, s2, threshold, copy=False): raise NotImplementedError()

    def apply_tr(self, tr, copy=False): raise NotImplementedError()

    def apply_backward_tr(self, tr, copy=False): raise NotImplementedError()

    def get_constraints(self): raise NotImplementedError()

    def __le__(self, s2): raise NotImplementedError()

    def toString(self, eq_symb="==", geq_symb=">="): raise NotImplementedError()

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

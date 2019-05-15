from . import AbstractState
from lpi import C_Polyhedron
from lpi import Expression
from interval import interval
from interval import inf

_eps = 1e-9

__all__ = ["IntervalAbstractState"]


class IntervalAbstractState(AbstractState):

    def __init__(self, arg1, bottom=False):
        if isinstance(arg1, C_Polyhedron):
            vars_ = arg1.get_variables()
            ispoly = True
        elif isinstance(arg1, list):
            vars_ = arg1
            ispoly = False
        else:
            raise TypeError("First argument must be list of variables or lpi.C_Polyhedron")
        if bottom:
            self._state = {v: interval() for v in vars_}
        elif ispoly:
            self._state = IntervalAbstractState.poly2interval(arg1, vars_, vars_)
        else:
            self._state = {v: interval([-inf, inf]) for v in vars_}

    def copy(self, copy=True):
        if copy:
            st = IntervalAbstractState([])
            st._state = dict(self._state)
            return st
        else:
            return self

    def lub(self, s2, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        state = {}
        for v in s1._state:
            a = s1._state[v]
            b = s2._state[v] if v in s2._state else interval()
            if len(a) == 0 and len(b) == 0:
                state[v] = interval()
            elif len(a) == 0:
                state[v] = b
            elif len(b) == 0:
                state[v] = a
            else:
                state[v] = interval.hull([a, b])
        s1._state = state
        return s1

    def widening_assign(self, s2, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        state = {}
        for v in self._state:
            a = s2._state[v] if v in s2._state else interval()
            b = s1._state[v]
            if len(a) == 0 or len(b) == 0:
                state[v] = interval()
                continue
            c1 = a[0].inf if a[0].inf <= b[0].inf else -inf
            c2 = a[-1].sup if a[-1].sup >= b[-1].sup else inf
            state[v] = interval([c1, c2])
        s1._state = state
        return s1

    def extrapolation_assign(self, s2, threshold, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        v1 = list(s1._state.keys())
        v2 = list(s2._state.keys())
        p1 = C_Polyhedron(constraints=s1.get_constraints(), variables=v1)
        p2 = C_Polyhedron(constraints=s2.get_constraints(), variables=v2)
        p1.extrapolation_assign(p2, threshold)
        s1._state = IntervalAbstractState.poly2interval(p1, v1, v1)
        return s1

    @classmethod
    def poly2interval(cls, poly, store_as, vars_):
        state = {}
        for i in range(len(vars_)):
            exp = Expression(vars_[i])
            b1 = poly.minimize(exp)
            c1 = -inf
            if b1['bounded']:
                c1 = b1['inf_n']
            b2 = poly.maximize(exp)
            c2 = inf
            if b2['bounded']:
                c2 = b2['sup_n']
            state[store_as[i]] = interval([c1, c2])
        return state

    def apply_tr(self, tr, copy=False):
        s1 = self.copy(copy)
        st = self._state
        poly_tr = tr["polyhedron"]
        all_vars = poly_tr.get_variables()
        poly = C_Polyhedron(poly_tr.get_constraints(), all_vars)
        n = len(self._state.keys())
        for v in st:
            if len(st[v]) == 0:
                a1 = 1
                a2 = -1
            else:
                a1 = st[v][0].inf
                a2 = st[v][-1].sup
            if a1 != -inf:
                poly.add_constraint(Expression(v) >= a1)
            if a2 != inf:
                poly.add_constraint(Expression(v) <= a2)

        s1._state = IntervalAbstractState.poly2interval(poly, all_vars[:n], all_vars[n:2 * n])
        return s1

    def apply_backward_tr(self, tr, copy=False):
        s1 = self.copy(copy)
        st = self._state
        poly_tr = tr["polyhedron"]
        all_vars = poly_tr.get_variables()
        poly = C_Polyhedron(poly_tr.get_constraints(), all_vars)
        n = len(self._state.keys())
        for v in st:
            pv = all_vars[all_vars.index(v) + n]
            if len(st[v]) == 0:
                a1 = 1
                a2 = -1
            else:
                a1 = st[v][0].inf
                a2 = st[v][-1].sup
            if a1 != -inf:
                poly.add_constraint(Expression(pv) >= a1)
            if a2 != inf:
                poly.add_constraint(Expression(pv) <= a2)

        s1._state = IntervalAbstractState.poly2interval(poly, all_vars[n:2 * n], all_vars[:n])
        return s1

    def get_constraints(self):
        cs = []
        for v in self._state:
            if len(self._state[v]) == 0:
                return [Expression(0) == Expression(1)]
            else:
                a1 = self._state[v][0].inf
                a2 = self._state[v][-1].sup
                if a1 == a2:
                    cs.append(Expression(v) == int(a1))
                    continue
                if a1 != -inf:
                    cs.append(Expression(v) >= int(a1))
                if a2 != inf:
                    cs.append(Expression(v) <= int(a2))
        return cs

    def __le__(self, s2):
        self._assert_same_type(s2)
        lte = True
        for v in self._state:
            value2 = s2._state[v] if v in s2._state else interval()
            if self._state[v] in value2:
                continue
            lte = False
            break
        return lte

    def toString(self, eq_symb="==", geq_symb=">="):
        return [c.toString(lambda x: x, int, eq_symb=eq_symb, geq_symb=geq_symb)
                for c in self.get_constraints()]

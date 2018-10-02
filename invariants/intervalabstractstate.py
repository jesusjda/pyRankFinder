from . import AbstractState
from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable
from interval import interval
from interval import inf

_eps = 1e-9


class IntervalState(AbstractState):

    _state = None
    dim = 0

    def __init__(self, arg1, bottom=False):
        self.dim = int(arg1)
        if bottom:
            self._state = [interval() for _ in range(self.dim)]
        else:
            self._state = [interval([-inf,inf]) for _ in range(self.dim)]

    def lub(self, s2, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        state = []
        for i in range(self.dim):
            a = s1._state[i]
            b = s2._state[i]
            if len(a) == 0 and len(b) == 0:
                state.append(interval())
            elif len(a) == 0:
                state.append(b)
            elif len(b) == 0:
                state.append(a)
            else:
                state.append(interval.hull([a,b]))
        s1._state = state
        return s1

    def widening(self, s2, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        state = []
        for i in range(self.dim):
            a = s2._state[i]
            b = s1._state[i]
            if len(a) == 0 or len(b) == 0:
                state.append(interval())
                continue
            c1 = a[0].inf if a[0].inf <= b[0].inf else -inf
            c2 = a[-1].sup if a[-1].sup >= b[-1].sup else inf
            state.append(interval([c1,c2]))
        s1._state = state
        return s1

    def apply_tr(self, tr, copy=False):
        s1 = self.copy(copy)
        st = self._state
        state = []
        poly_tr = tr["tr_polyhedron"]
        poly = C_Polyhedron(poly_tr.get_constraints())

        for i in range(self.dim):
            if len(st[i]) == 0:
                a1 = 1
                a2 = -1
            else:
                a1 = st[i][0].inf
                a2 = st[i][-1].sup
            if a1 != -inf:
                poly.add_constraint(Variable(i) >= a1 )
            if a2 != inf:
                poly.add_constraint(Variable(i) <= a2 )

        for i in range(self.dim):
            exp = Linear_Expression(Variable(self.dim + i))
            b1 = poly.minimize(exp)
            c1 = -inf
            if b1['bounded']:
                c1 = b1['inf_n']
            b2 = poly.maximize(exp)
            c2 = inf
            if b2['bounded']:
                c2 = b2['sup_n']
            state.append(interval([c1,c2]))
        s1._state = state
        return s1

    def get_constraints(self):
        cs = Constraint_System()
        for i in range(self.dim):
            if len(self._state[i]) == 0:
                cs.insert(Linear_Expression(0) == Linear_Expression(1))
            else:
                a1 = self._state[i][0].inf
                a2 = self._state[i][-1].sup
                if a1 == a2:
                    cs.insert(Variable(i) == int(a1))
                    continue
                if a1 != -inf:
                    cs.insert(Variable(i) >= int(a1) )
                if a2 != inf:
                    cs.insert(Variable(i) <= int(a2) )
        return cs

    def __le__(self, s2):
        self._assert_same_type(s2)
        lte = True
        for i in range(self.dim):
            if self._state[i] in s2._state[i]:
                continue
            lte = False
            break
        return lte

    def toString(self, vars_name=None, eq_symb="==", geq_symb=">="):
        if vars_name is None:
            vars_name = ['x'+str(i) for i in range(self.dim*2)]
        cads = []
        for i in range(self.dim):
            if len(self._state[i]) == 0:
                cads = ["1 "+eq_symb+" 0"]
                break
            a1 = self._state[i][0].inf
            a2 = self._state[i][-1].sup
            if abs(a1 - a2) < _eps:
                cads.append(vars_name[i]+""+eq_symb+""+str(int(a1)))
            else:
                if a1 != -inf:
                    cads.append(vars_name[i]+" "+geq_symb+" "+str(int(a1)))
                if a2 != inf:
                    cads.append(str(int(a2))+" "+geq_symb+" "+vars_name[i])
        return cads



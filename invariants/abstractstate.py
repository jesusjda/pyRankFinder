from copy import deepcopy
from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable
from ppl import Variables_Set
from interval import interval
from interval import inf

_eps = 1e-9

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

    def widening(self, s2, copy=False):
        pass

    def apply_tr(self, tr, copy=False):
        pass

    def get_constraints(self):
        pass

    def __le__(self, s2):
        pass

class PolyhedraState(AbstractState):

    _state = None

    def __init__(self, arg1, bottom=False):
        if isinstance(arg1, C_Polyhedron):
            dim = arg1.space_dimension()
            cs = arg1.get_constraints()
        else:
            try:
                dim = int(arg1)
                cs = Constraint_System()
            except ValueError:
                raise TypeError("Only int or lpi.C_Polyhedron")
        self._state = C_Polyhedron(cs, dim=dim)
        if bottom:
            false = Linear_Expression(0) == Linear_Expression(1)
            self._state.add_constraint(false)
        self._state.minimized_constraints()

    def lub(self, s2, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        s1._state.poly_hull_assign(s2._state)
        return s1

    def widening(self, s2, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        s1._state.widening_assign(s2._state)
        return s1

    def apply_tr(self, tr, copy=False):
        s1 = self.copy(copy)
        poly_tr = tr["tr_polyhedron"]
        m = poly_tr.get_dimension()
        n = s1._state.get_dimension()
        s1._state.add_dimensions(m - n)
        s1._state.intersection_assign(poly_tr)
        var_set = Variables_Set()
        for i in range(0, n):  # Vars from 0 to n-1 inclusive
            var_set.insert(Variable(i))
        # (local variables)
        for i in range(2 * n, m):  # Vars from 2*n to m-1 inclusive
            var_set.insert(Variable(i))
        s1._state.remove_dimensions(var_set)
        return s1

    def get_constraints(self):
        return self._state.get_constraints()

    def __le__(self, s2):
        self._assert_same_type(s2)
        return self._state <= s2._state

    def toString(self, vars_name=None, eq_symb="==", geq_symb=">="):
        return self._state.toString(vars_name=vars_name, eq_symb=eq_symb, geq_symb=geq_symb)

    def __repr__(self):
        return "{{{}}}".format(", ".join(self.toString()))


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
                    cs.insert(Variable(i) == a1)
                    continue
                if a1 != -inf:
                    cs.insert(Variable(i) >= a1 )
                if a2 != inf:
                    cs.insert(Variable(i) <= a2 )
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
                cads.append(vars_name[i]+""+eq_symb+""+str(a1))
            else:
                if a1 != -inf:
                    cads.append(vars_name[i]+" "+geq_symb+" "+str(a1))
                if a2 != inf:
                    cads.append(str(a2)+" "+geq_symb+" "+vars_name[i])
        return cads

    def __repr__(self):
        return "{{{}}}".format(", ".join(self.toString()))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

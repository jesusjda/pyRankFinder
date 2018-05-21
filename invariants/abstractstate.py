from copy import deepcopy
from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable
from ppl import Variables_Set


class AbstractState(object):

    def __init__(self, *kwargs):
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


class ConstraintState(AbstractState):

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

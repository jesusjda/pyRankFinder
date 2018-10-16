from . import AbstractState
from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable
from ppl import Variables_Set

__all__ = ["PolyhedraAbstractState"]

class PolyhedraAbstractState(AbstractState):

    _state = None

    def __init__(self, arg1, bottom=False):
        if isinstance(arg1, C_Polyhedron):
            dim = arg1.get_dimension()
            cs = arg1.get_constraints()
        elif isinstance(arg1, Constraint_System):
            dim = arg1.space_dimension()
            cs = arg1
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

    def widening_assign(self, s2, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        s1._state.widening_assign(s2._state)
        return s1
    
    def extrapolation_assign(self, s2, threshold, copy=False):
        self._assert_same_type(s2)
        s1 = self.copy(copy)
        s1._state.extrapolation_assign(s2._state, threshold)
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

    def apply_backward_tr(self, tr, copy=False):
        s1 = self.copy(copy)
        poly_tr = tr["tr_polyhedron"]
        m = poly_tr.get_dimension()
        n = s1._state.get_dimension()
        # move x to x'
        for i in range(0, n):
            s1._state.expand_space_dimension(Variable(i), 1)
            s1._state.unconstraint(Variable(i))
        s1._state.add_dimensions(m - 2*n)
        s1._state.intersection_assign(poly_tr)
        var_set = Variables_Set()
        for i in range(n, m):  # Vars from n to m-1 inclusive
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


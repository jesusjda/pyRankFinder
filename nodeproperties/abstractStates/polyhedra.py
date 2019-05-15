from . import AbstractState
from lpi import C_Polyhedron
from lpi import Expression

__all__ = ["PolyhedraAbstractState"]


class PolyhedraAbstractState(AbstractState):

    def __init__(self, arg1, bottom=False):
        if isinstance(arg1, C_Polyhedron):
            vars_ = arg1.get_variables()
            cs = arg1.get_constraints()
        elif isinstance(arg1, list):
            vars_ = arg1
            cs = []
        else:
            raise TypeError("First argument must be list of variables or lpi.C_Polyhedron")
        self._state = C_Polyhedron(constraints=cs, variables=vars_)
        if bottom:
            false = Expression(0) == Expression(1)
            self._state.add_constraint(false)
        self._state.minimized_constraints()

    def copy(self, copy=True):
        if copy:
            return PolyhedraAbstractState(self._state)
        else:
            return self

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
        poly_tr = tr["polyhedron"]
        m = poly_tr.get_dimension()
        vars_ = poly_tr.get_variables()
        n = s1._state.get_dimension()
        p = s1._state.copy()
        p.add_dimensions(m - n, vars_[n:])
        p.add_constraints(poly_tr.get_constraints())
        p = p.project(vars_[n:2 * n])
        s1._state = C_Polyhedron(constraints=p.get_constraints(vars_[:n]), variables=vars_[:n])
        return s1

    def apply_backward_tr(self, tr, copy=False):
        s1 = self.copy(copy)
        poly_tr = tr["polyhedron"]
        m = poly_tr.get_dimension()
        n = s1._state.get_dimension()
        vars_ = poly_tr.get_variables()
        p = s1._state.copy()
        p.add_dimensions(m - n, vars_[n:])
        # swap x and x'
        vs = vars_[n:2 * n] + vars_[:n] + vars_[2 * n:]
        p.add_constraints(poly_tr.get_constraints(vs))
        p = p.project(vars_[n:2 * n])
        s1._state = C_Polyhedron(constraints=p.get_constraints(vars_[:n]), variables=vars_[:n])
        return s1

    def get_constraints(self):
        return self._state.get_constraints()

    def __le__(self, s2):
        self._assert_same_type(s2)
        return self._state <= s2._state

    def toString(self, eq_symb="==", geq_symb=">="):
        return self._state.toString(eq_symb=eq_symb, geq_symb=geq_symb)

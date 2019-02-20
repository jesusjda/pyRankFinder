from lpi import C_Polyhedron
from .manager import Algorithm
from .manager import Manager
from termination.output import Output_Manager as OM
from .utils import get_free_name
from termination import farkas
from termination.result import Result
from termination.result import TerminationResult


class FixPoint(Algorithm):
    ID = "fixpoint"
    NAME = "fixpoint"
    DESC = "non termination looking for a fixpoint"

    def __init__(self, properties={}):
        self.props = properties

    @classmethod
    def use_close_walk(cls):
        return True

    def run(self, cfg, close_walk=[]):
        """
        looking for a fixpoint in a close walk:
        [n0] -(x, xP)-> [n1] -(xP, x2)-> [n2] -(x2, x)-> [n0]
        """
        from lpi import Solver
        OM.printif(1, "--> with " + self.NAME)
        global_vars = cfg.get_info("global_vars")
        Nvars = int(len(global_vars) / 2)
        vs = global_vars[:Nvars]

        all_vars = [] + vs
        all_vars += get_free_name(vs, name="X", num=Nvars * (len(close_walk) - 1))
        all_vars += vs
        taken_vars = all_vars
        tr_idx = 0
        cons = []
        for tr in close_walk:
            local_vars = get_free_name(taken_vars, name="Local", num=len(tr["local_vars"]))
            tr_vars = all_vars[tr_idx:tr_idx + 2 * Nvars] + local_vars
            taken_vars += local_vars
            cs = [c for c in tr["polyhedron"].get_constraints(tr_vars)
                  if c.is_linear()]
            cons += cs
            tr_idx += Nvars
        s = Solver()
        s.add(cons)
        point, __ = s.get_point(taken_vars)
        response = Result()
        if point is not None:
            fixpointvalue = {v: point[v] for v in vs}
            OM.printif(1, "FixPoint Found")
            response.set_response(status=TerminationResult.NONTERMINATE,
                                  info="FixPoint Found",
                                  close_walk=close_walk,
                                  fixpoint=fixpointvalue)
        else:
            OM.printif(1, "No fixpoint found.")
            response.set_response(status=TerminationResult.UNKNOWN,
                                  info="No fixpoint found.")
        return response


class MonotonicRecurrentSets(Algorithm):
    ID = "monotonicrecset"
    NAME = "monotonic recurrent set"
    DESC = "Based on MphRF"

    def __init__(self, properties={}):
        self.props = properties

    @classmethod
    def use_close_walk(cls):
        return True

    @classmethod
    def generate(cls, data):
        if(len(data) == 0 or
           data[0] != cls.ID):
            return None

        properties = {
            "name": data[0],
            "max_depth": 5
        }
        data = data[1::]
        if len(data) == 0:
            return cls(properties)
        return None

    def run(self, cfg, close_walk=[]):
        """
        looking for a Monotonic Recurrent Set in a close walk:
        [n0] -(x0, x1)-> [n1] -(x1, x2)-> [n2] -(x2, xP)-> [n0]
        """
        from lpi import Expression
        from ppl import Variable
        OM.printif(1, "--> with " + self.NAME)
        global_vars = cfg.get_info("global_vars")
        Nvars = int(len(global_vars) / 2)
        vs = global_vars[:Nvars]
        pvs = global_vars[Nvars:]

        cicle_constraints = []
        all_vars = [] + vs
        all_vars += get_free_name(global_vars, name="X", num=Nvars * (len(close_walk) - 1))
        all_vars += pvs
        taken_vars = all_vars
        tr_idx = 0
        cons = []
        for tr in close_walk:
            local_vars = get_free_name(taken_vars, name="Local", num=len(tr["local_vars"]))
            tr_vars = all_vars[tr_idx:tr_idx + 2 * Nvars] + local_vars
            taken_vars += local_vars
            cons += [c for c in tr["polyhedron"].get_constraints(tr_vars)
                     if c.is_linear()]
            tr_idx += Nvars
        tr_poly_p = None
        tr_poly = C_Polyhedron(constraints=cons, variables=taken_vars)
        response = Result()
        depth = 0
        while depth < self.get_prop("max_depth"):
            if tr_poly.is_empty():
                OM.printif(1, "Empty polyhedron.")
                response.set_response(status=TerminationResult.UNKNOWN,
                                      close_walk=close_walk,
                                      info="No Recurrent Set Found. Empty Polyhedron.")
                return response
            Mcons = len(tr_poly.get_constraints())
            f = get_free_name(taken_vars, name="a_", num=Nvars + 1)
            taken_vars += f
            lambdas = get_free_name(taken_vars, name="l", num=Mcons)
            taken_vars += lambdas
            cicle_constraints = farkas.f(tr_poly,
                                         [Expression(v) for v in lambdas],
                                         [Expression(v) for v in f], 0)
            cicle_poly = C_Polyhedron(constraints=cicle_constraints, variables=f + lambdas)
            generators = cicle_poly.get_generators()
            tr_poly_p = tr_poly.copy()
            generators = [g for g in generators if not g.is_point()]
            OM.printif(3, "Generators of farkas polyhedron", generators)

            for g in generators:
                exp = Expression(0)
                for i in range(Nvars):
                    coef = int(g.coefficient(Variable(i + 1)))
                    if coef != 0:
                        exp += coef * Expression(vs[i]) - coef * Expression(pvs[i])
                if g.is_ray():
                    tr_poly_p.add_constraint(exp <= 0)
                elif g.is_line():
                    tr_poly_p.add_constraint(exp == 0)

            if tr_poly_p.contains(tr_poly):
                OM.printif(1, "Recurrent Set Found:\n" +
                           str(tr_poly))
                response.set_response(status=TerminationResult.NONTERMINATE,
                                      info="Recurrent Set Found:",
                                      close_walk=close_walk,
                                      rec_set=tr_poly)
                return response
            tr_poly = tr_poly_p
            depth += 1
        OM.printif(1, "No Recurrent Set Found.")

        response.set_response(status=TerminationResult.UNKNOWN,
                              close_walk=close_walk,
                              info="No Recurrent Set Found. Max iterations.")
        return response


class NonTermination(Manager):
    ALGORITHMS = [FixPoint, MonotonicRecurrentSets]
    ID = "non"

    @classmethod
    def get_algorithm(cls, token):
        if isinstance(token, str):
            data = token.split("_")
        else:
            data = token
        for opt in cls.ALGORITHMS:
            alg = opt.generate(data)
            if alg is None:
                continue
            return alg
        raise ValueError("Not Valid token")

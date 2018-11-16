from z3 import Solver
from z3 import Real
from z3 import substitute
from z3 import sat
from .manager import Algorithm
from .manager import Manager
from termination.output import Output_Manager as OM
from .utils import get_z3_transition_polyhedron
from .utils import generate_prime_names
from .utils import generate_names

from termination import farkas
from termination.result import Result
from termination.result import TerminationResult


class FixPoint(Algorithm):
    ID = "fixpoint"
    NAME = "fixpoint"
    DESC = "non termination looking for a fixpoint"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, close_walk):
        try:
            init_node = cfg.get_info("init_node")
        except:
            init_node = cfg.get_edges()[0]["source"]

        OM.printif(1, "--> with "+self.NAME)
        global_vars = cfg.get_info("global_vars")
        Nvars = int(len(global_vars) / 2)
        vs = global_vars[:Nvars]
        pvs = global_vars[Nvars:]

        s = Solver()
        X = vs[:]
        XP = pvs[:]
        used_names = pvs
        if len(close_walk) == 1:
            for c in get_z3_transition_polyhedron(close_walk[0], vs + pvs):
                s.add(c)
        for tr in close_walk[:-1]:
            used_names += tr["local_vars"]
            XP = generate_prime_names(vs,used_names)
            used_names += XP
            rename = [(Real(c), Real(d)) for c, d in zip(vs, X)]
            rename += [(Real(c), Real(d)) for c, d in zip(pvs, XP)]
            for c in get_z3_transition_polyhedron(tr, vs + pvs):
                s.add(substitute(c, rename))
            X = XP
        rename = [(Real(c), Real(d)) for c, d in zip(vs, XP)]
        rename += [(Real(c), Real(d)) for c, d in zip(pvs, vs)]
        for c in get_z3_transition_polyhedron(close_walk[-1], vs + pvs):
            s.add(substitute(c, rename))
        response = Result()
        if s.check() == sat:
            m = s.model()
            OM.printif(1, "FixPoint Found")
            response.set_response(status=TerminationResult.NONTERMINATE,
                                  info="FixPoint Found",
                                  close_walk=close_walk,
                                  model=m)
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

    def run(self, cfg, close_walk):
        from ppl import Constraint_System
        from ppl import Variable
        from ppl import Linear_Expression
        from lpi import C_Polyhedron
        from copy import deepcopy
        OM.printif(1, "--> with "+self.NAME)
        global_vars = cfg.get_info("global_vars")
        Nvars = int(len(global_vars) / 2)
        vs = global_vars[:Nvars]
        pvs = global_vars[Nvars:]
        lvs = []
        trvs_idx = []
        countVar = 0

        for tr in close_walk:
            lvs += tr["local_vars"]
            trvs_idx.append(countVar)
            countVar += Nvars
        
        farkas_constraints = []
        countVar -= Nvars
        dummy_var = generate_names(["local"+str(i) for i in range(countVar)],global_vars+lvs)
        countVar = 0
        ppl_cons = []
        for tr in close_walk:
            all_vars = dummy_var[:countVar]+vs+pvs+dummy_var[countVar:]+lvs
            ppl_cons += [c.transform(all_vars, lib="ppl")
                         for c in tr["constraints"] if c.is_linear()]
            countVar += Nvars
        tr_poly_p = None
        tr_poly = C_Polyhedron(Constraint_System(ppl_cons), dim=len(all_vars))
        response = Result()
        depth = 0
        pvs_idx = len(close_walk)*(Nvars)
        while depth < self.get_prop("max_depth"):
            if tr_poly.is_empty():
                OM.printif(1, "Empty polyhedron.")
                response.set_response(status=TerminationResult.UNKNOWN,
                                      close_walk=close_walk,
                                      info="No Recurrent Set Found. Empty Polyhedron.")
                return response
            Mcons = len(tr_poly.get_constraints())
            f = [Variable(i) for i in range(0, Nvars + 1)]
            countVar = Nvars + 1
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            farkas_constraints = farkas.f(tr_poly, lambdas, f, 0)
            farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
            generators = farkas_poly.get_generators()
            tr_poly_p = deepcopy(tr_poly)
            generators = [g for g in generators if g.is_ray()]
            OM.printif(2, generators)
            for g in generators:
                exp = Linear_Expression(0)
                for i in range(Nvars):
                    coef = g.coefficient(Variable(i+1))
                    exp += coef*Variable(i) - coef*Variable(pvs_idx+i)

                tr_poly_p.add_constraint(exp <= 0)

            if tr_poly_p.contains(tr_poly):
                OM.printif(1, "Recurrent Set Found:\n" +
                           OM.tostr(tr_poly.get_constraints(), vs+dummy_var+pvs+lvs))
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

from z3 import Solver
from z3 import Real
from z3 import substitute
from z3 import sat
from .manager import Algorithm
from .manager import Manager
from termination.output import Output_Manager as OM
from .utils import get_z3_transition_polyhedron


class Renaming(Algorithm):
    ID = "rename"
    NAME = "rename"
    DESC = "Cicle non termination via renaming"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, use_z3=None):
        cycles = [c for c in cfg.simple_cycles()]
        if not cycles:
            return []
        global_vars = cfg.get_info("global_vars")
        Nvars = int(len(global_vars)/2)
        vs = global_vars[:Nvars]
        pvs = global_vars[Nvars:]
        solutions = []
        s = Solver()
        
        cys = "\n\t".join([" -> ".join(c) for c in cycles])
        OM.printif(2, "Cycles:\n\t"+cys)
        for cycle in cycles:
            cys = ' -> '.join(cycle)
            OM.printif(2, "Analyzing cycle: "+str(cys))
            sols = []
            if len(cycle) == 1:
                trs = cfg.get_edges(source=cycle[0], target=cycle[0])
                for tr in trs:
                    s.push()
                    rename = [(Real(c), Real(d)) for c,d in zip(vs, pvs)]
                    rename += [(Real(c), Real(d)) for c,d in zip(pvs, vs)]
                    for c in get_z3_transition_polyhedron(tr, vs+pvs):
                        s.add(c)
                        s.add(substitute(c, rename))
                    if s.check() == sat:
                        m = s.model()
                        sols += [(cycle, m)]
                    s.pop()
            else:
                names = [vs, pvs]
                ppvs = pvs
                primetoken = "'"
                for _ in range(2, len(cycle)):
                    ppvs = [v+primetoken for v in ppvs]
                    names.append(ppvs)
                names.append(vs)
                nodes = cycle + [cycle[0]]
                sols = self._rec_rename(s, cfg, vs, pvs, nodes, names)
            if sols:
                OM.printif(1, cycle, ":", sols)
                solutions += [(cycle, sol) for sol in sols]
        return solutions

    def _rec_rename(self, solver, cfg, vs, pvs, nodes, names):
        if len(nodes) == 1:
            if solver.check() == sat:
                return [solver.model()]
            else:
                return None
        src = nodes[0]
        trg = nodes[1]
        trs = cfg.get_edges(source=src, target=trg)
        solutions = []
        for tr in trs:
            solver.push()
            rename = [(Real(c),Real(d)) for c,d in zip(vs,names[0])]
            rename += [(Real(c),Real(d)) for c,d in zip(pvs,names[1])]
            for c in get_z3_transition_polyhedron(tr, vs+pvs):
                solver.add(substitute(c, rename))
            sols = self._rec_rename(solver, cfg, vs, pvs, nodes[1::], names[1::])
            if sols:
                solutions += sols
            solver.pop()
        return solutions


class NonTermination(Manager):
    ALGORITHMS = [Renaming]
    ID = "non"

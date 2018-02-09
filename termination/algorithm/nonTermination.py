from ppl import Variable
from termination.result import TerminationResult

from .manager import Algorithm
from .manager import Manager

from .utils import max_dim


class BASIC(Algorithm):
    ID = "basic"
    NAME = "basic"
    DESC = "Cicle non termination via basic, no changes"

    def __init__(self, properties={}):
        self.props = properties

    def run(self, cfg, different_template=False, use_z3=None):
        cycles = cfg.cycle_basis()
        if not cycles:
            return TerminationResult.TERMINATE
        dim = max_dim(cfg.get_edges())
        Nvars = int(dim/2)
        for c in cycles:
            if len(c) == 1:
                trs = cfg.get_edges(src=c[0], trg=c[0])
                for tr in trs:
                    poly = tr["polyhedron"]
                    if poly.is_empty():
                        continue
                    for i in range(Nvars):
                        poly.add_constraint(Variable(i) == Variable(Nvars+i))
                    if not poly.is_empty():
                        return TerminationResult.NONTERMINATE
        return TerminationResult.UNKNOWN


class NonTermination(Manager):
    ALGORITHMS = []
    ID = "non"

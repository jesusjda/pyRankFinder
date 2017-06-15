from TerminationAlgorithm import *

from ppl import Linear_Expression
from ppl import Variable
from ppl import Constraint_System
from ppl import Constraint
from LPi import C_Polyhedron


class LexAlgorithm(TerminationAlgorithm):

    _data = {}

    def ranking(self, data):
        self._data = data.copy()
        if not("cfg" in self._data):
            raise Exception(self.__class__+" needs a ControlFlowGraph.")
        cfg = self._data["cfg"]
        transitions = cfg.get_edges()
        rfs = {}
        no_ranked_trs = list(transitions)
        i = 0
        while no_ranked_trs:  # while not empty
            i += 1
            result = self.compute(no_ranked_trs)
            if result['status'] == "noRanked":
                return {'status': "noRanked1",
                        'error': "A set of transitions cannot be ranked",
                        'rfs': rfs,
                        'trs': no_ranked_trs}
            elif result['status'] == "Fail":
                pass  # return irrecuperable error
            elif result['status'] == "Ranked":
                if len(no_ranked_trs) <= len(result['no_ranked_tr']):
                    return {'status': "noRanked2",
                            'error': "A set of transitions cannot be ranked",
                            'rfs': rfs,
                            'trs': no_ranked_trs}
                no_ranked_trs = result['no_ranked_tr']
                for node in result['rfs']:
                    if not(node in rfs):
                        rfs[node] = []
                    rfs[node].append(result['rfs'][node])

        return {'status': "Ranked",
                'rfs': rfs,
                'vars_name': cfg.get_var_name()}

    def compute(self, transitions):
        dim = self._max_dim(transitions)
        Nvars = dim / 2
        shifter = 0
        if ("different_template" in self._data and
            self._data["different_template"]):
            shifter = Nvars + 1
        # farkas Variables
        rfvars = {}
        deltas = []
        # farkas constraints
        farkas_constraints = []
        # return objects
        rfs = {}  # rfs coefficients (result)
        no_ranked = []  # transitions sets no ranked by rfs
        # other stuff
        nodeList = {}
        countVar = 0
        # 1.1 - store rfs variables
        for tr in transitions:
            if not(tr["source"] in nodeList):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["source"]] = f
                countVar += shifter
            if not(tr["target"] in nodeList):
                f = [Variable(i)
                     for i in range(countVar, countVar + Nvars + 1)]
                rfvars[tr["target"]] = f
                countVar += shifter
        countVar += Nvars + 1
        print("rfs", rfvars, countVar)
        # 1.2 - store delta variables
        deltas = {transitions[i]["name"]: Variable(countVar + i)
                  for i in range(len(transitions))}
        countVar += len(transitions)
        print("deltas", deltas, countVar)
        for tr in transitions:
            rf_s = rfvars[tr["source"]]
            rf_t = rfvars[tr["target"]]
            Mcons = len(tr["tr_polyhedron"].get_constraints())

            # f_s >= 0
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            print("lambdas", lambdas, countVar)
            farkas_constraints += self._f(tr["tr_polyhedron"], lambdas,
                                          rf_s, 0)

            # f_s - f_t >= delta[tr]
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            farkas_constraints += self._df(tr["tr_polyhedron"], lambdas,
                                           rf_s, rf_t, deltas[tr["name"]])

            # 0 <= delta[tr] <= 1
            farkas_constraints += [0 <= deltas[tr["name"]],
                                   deltas[tr["name"]] <= 1]

        poly = C_Polyhedron(Constraint_System(farkas_constraints))
        exp = sum([deltas[tr] for tr in deltas])
        print(poly.get_constraints())
        print(exp)
        result = poly.maximize(exp)
        print(result)
        if not result['bounded']:
            print("unbo")
            return {'status': "noRanked", 'error': "Unbounded"}
        point = result["generator"]
        if point is None:
            print("is none")
            return {'status': "noRanked", 'error': "who knows"}

        for node in rfvars:
            rfs[node] = ([point.coefficient(c) for c in rfvars[node][1::]],
                         point.coefficient(rfvars[node][0]))

            no_ranked = [tr for tr in transitions
                         if point.coefficient(deltas[tr["name"]]) == 0]
        return {'status': "Ranked",
                'rfs': rfs,
                'no_ranked_tr': no_ranked}

    def _max_dim(self, edges):
        maximum = 0
        for e in edges:
            d = e["tr_polyhedron"].get_dimension()
            if d > maximum:
                maximum = d
        return maximum

    def print_result(self, result):
        if result['status'] == "Ranked":
            print(result['rfs'])
            for node in result['rfs']:
                for i in range(len(result['rfs'][node])):
                    coeffs = result['rfs'][node][i][0]
                    inh = result['rfs'][node][i][1]
                    self._print_function("f_"+node+"_"+str(i),
                                         result['vars_name'],
                                         coeffs, inh)
        else:
            print("Response: "+result['status'])
            print(result)

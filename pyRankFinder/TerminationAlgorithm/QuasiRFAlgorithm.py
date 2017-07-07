from ppl import Variable
from ppl import Linear_Expression
from LPi import C_Polyhedron
from Farkas import Farkas

class QuasiRF:

    def computeQRF(self, transitions):
        raise Exception("Not implemented yet")

class QuasiLinearRF(QuasiRF):

    def computeQRF(self, transitions):
        dim = self._max_dim(transitions)
        Nvars = dim / 2
        shifter = 0
        if("different_template" in self._data and
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
        # print("rfs", rfvars, countVar)
        # 1.2 - store delta variables
        deltas = {transitions[i]["name"]: Variable(countVar + i)
                  for i in range(len(transitions))}
        countVar += len(transitions)
        # print("deltas", deltas, countVar)
        for tr in transitions:
            rf_s = rfvars[tr["source"]]
            rf_t = rfvars[tr["target"]]
            Mcons = len(tr["tr_polyhedron"].get_constraints())

            # f_s >= 0
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            # print("lambdas", lambdas, countVar)
            farkas_constraints += Farkas.f(tr["tr_polyhedron"], lambdas,
                                           rf_s, 0)

            # f_s - f_t >= delta[tr]
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            countVar += Mcons
            farkas_constraints += Farkas.df(tr["tr_polyhedron"], lambdas,
                                           rf_s, rf_t, deltas[tr["name"]])

            # 0 <= delta[tr] <= 1
            farkas_constraints += [0 <= deltas[tr["name"]],
                                   deltas[tr["name"]] <= 1]

        poly = C_Polyhedron(Constraint_System(farkas_constraints))
        exp = sum([deltas[tr] for tr in deltas])
        result = poly.maximize(exp)
        if not result['bounded']:
            return {'status': "noRanked", 'error': "Unbounded"}
        point = result["generator"]
        zeros = True
        for c in point.coefficients():
            if c != 0:
                zeros = False
        if point is None or zeros:
            return {'status': "noRanked", 'error': "who knows"}

        for node in rfvars:
            rfs[node] = ([point.coefficient(c) for c in rfvars[node][1::]],
                         point.coefficient(rfvars[node][0]))

            no_ranked = [tr for tr in transitions
                         if point.coefficient(deltas[tr["name"]]) == 0]
        return {'status': "Ranked",
                'rfs': rfs,
                'no_ranked_tr': no_ranked}

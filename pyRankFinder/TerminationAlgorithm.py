from ppl import Linear_Expression
from ppl import Variable
from ppl import Constraint_System
from ppl import Constraint
from LPi import C_Polyhedron
import Farkas
import Termination


def _max_dim(edges):
    maximum = 0
    for e in edges:
        d = e["tr_polyhedron"].get_dimension()
        if d > maximum:
            maximum = d
    return maximum


def LinearRF(data):
    transitions = data["transitions"]

    dim = _max_dim(transitions)
    Nvars = dim / 2
    response = Termination.Result(vars_name=data["vars_name"])

    shifter = 0
    if "different_template" in data and data["different_template"]:
        shifter = Nvars + 1
    # farkas Variables
    rfvars = {}
    # farkas constraints
    farkas_constraints = []
    # rfs coefficients (result)
    rfs = {}
    # other stuff
    nodeList = {}
    countVar = 0
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

    num_constraints = [len(e["tr_polyhedron"].get_constraints())
                       for e in transitions]

    for tr in transitions:
        rf_s = rfvars[tr["source"]]
        rf_t = rfvars[tr["target"]]
        Mcons = len(tr["tr_polyhedron"].get_constraints())

        # f_s >= 0
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons + 1
        farkas_constraints += Farkas.f(tr["tr_polyhedron"], lambdas,
                                       rf_s, 0)

        # f_s - f_t >= 1
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons + 1
        farkas_constraints += Farkas.df(tr["tr_polyhedron"], lambdas,
                                        rf_s, rf_t, 1)

    poly = C_Polyhedron(Constraint_System(farkas_constraints))
    point = poly.get_point()
    if point is None:
        response.set_response(found=False,
                              info="Farkas Polyhedron is empty.")
        return response

    for node in rfvars:
        rfs[node] = ([point.coefficient(c) for c in rfvars[node][1::]],
                     point.coefficient(rfvars[node][0]))

    response.set_response(found=True,
                          rfs=rfs)
    return response


def LexicographicRF(data):
    response = Termination.Result(vars_name=data["vars_name"])
    transitions = data["transitions"]
    # print(transitions)
    rfs = {}
    no_ranked_trs = transitions
    i = 0
    config = data["inner_alg"].copy()
    config["vars_name"] = data["vars_name"]

    while no_ranked_trs:  # while not empty
        i += 1
        config["transitions"] = [tr.copy() for tr in no_ranked_trs]
        result = Termination.run(config)
        if result.error():
            return result
        elif not result.found():
            response.set_response(found=False,
                                  info=result.get("info"),
                                  rfs=rfs,
                                  pending_trs=no_ranked_trs)
            return response
        else:
            pending_trs = result.get("pending_trs")
            if False and len(no_ranked_trs) <= len(pending_trs):
                response.set_response(found=False,
                                      info="No decreasing",
                                      rfs=rfs,
                                      pending_trs=no_ranked_trs)
                return response
            res_rfs = result.get("rfs")
            for node in res_rfs:
                if not(node in rfs):
                    rfs[node] = []
                rfs[node].append(res_rfs[node])
            no_ranked_trs = pending_trs

    response.set_response(found=True,
                          rfs=rfs)
    return response


def compute_adfg_QLRF(data):
    response = Termination.Result(vars_name=data["vars_name"])
    transitions = data["transitions"]

    dim = _max_dim(transitions)
    Nvars = dim / 2
    shifter = 0
    if data["different_template"]:
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
        # print("lambdas", lambdas, countVar)
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
        response.set_response(found=False,
                              info="Unbound polyhedron")
        return response
    point = result["generator"]
    zeros = True
    for c in point.coefficients():
        if c != 0:
            zeros = False
    if point is None or zeros:
        response.set_response(found=False,
                              info="F === 0 "+str(point))
        return response

    for node in rfvars:
        rfs[node] = ([point.coefficient(c) for c in rfvars[node][1::]],
                     point.coefficient(rfvars[node][0]))

        no_ranked = [tr for tr in transitions
                     if point.coefficient(deltas[tr["name"]]) == 0]

    response.set_response(found=True,
                          info="mm",
                          rfs=rfs,
                          pending_trs=no_ranked)
    return response


def compute_bg_QLRF(data):
    response = Termination.Result(vars_name=data["vars_name"])
    transitions = data["transitions"]

    dim = _max_dim(transitions)
    Nvars = dim / 2
    shifter = 0
    size_rfs = 0
    if data["different_template"]:
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
    size_rfs = countVar
    # print("rfs", rfvars, countVar)
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

        # f_s - f_t >= 1
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        # print("lambdas", lambdas, countVar)
        farkas_constraints += Farkas.df(tr["tr_polyhedron"], lambdas,
                                        rf_s, rf_t, 0)
    poly = C_Polyhedron(Constraint_System(farkas_constraints))
    result = poly.get_relative_interior_point(size_rfs)
    if result is None:
        response.set_response(found=False,
                              info="No relative interior point")
        return response
    for node in rfvars:
        rfs[node] = ([result[c.id()] for c in rfvars[node][1::]],
                     result[(rfvars[node][0]).id()])

    response.set_response(found=False,
                          info="No non-trivial RF")

    # check if rfs are non-trivial
    nonTrivial = False
    for tr in transitions:
        rfvars_s = rfvars[tr["source"]]
        rfvars_t = rfvars[tr["target"]]
        rf_s = rfs[tr["source"]]
        rf_t = rfs[tr["target"]]
        poly = tr["tr_polyhedron"]
        df = 0
        constant = rf_s[1] - rf_t[1]
        for i in range(Nvars):
            df += Variable(i) * rf_s[0][i]
            df -= Variable(Nvars + i) * rf_t[0][i]
        answ = poly.maximize(df)

        if(not answ["bounded"] or
           answ["sup_n"] > -constant):
            nonTrivial = True
            break

    if nonTrivial:
        no_ranked = []
        for tr in transitions:
            poly = tr["tr_polyhedron"]
            cons = poly.get_constraints()
            cons.insert(df+constant == 0)
            newpoly = C_Polyhedron(cons)
            if not newpoly.is_empty():
                tr["tr_polyhedron"] = newpoly
                tr["label"] = (tr["label"][:-1] + str(df) +
                               "+" + str(constant) + "==0\n}")
                no_ranked.append(tr)
        response.set_response(found=True,
                              info="found",
                              rfs=rfs,
                              pending_trs=no_ranked)
        return response
    response.set_response(found=False,
                          info="rf found was the trivial")
    return response

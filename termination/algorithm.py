from ppl import Linear_Expression
from ppl import Variable
from ppl import Constraint_System
from ppl import Constraint
from lpi import C_Polyhedron
from . import farkas
from .result import Result
from .output import Output_Manager as OM


def run(data):
    OM.printif(3, data)
    config = data.copy()
    alg = config["algorithm"]['name']
    if alg == "lrf_pr":
        return LinearRF(config)
    elif alg == "qlrf_adfg":
        return compute_adfg_QLRF(config)
    elif alg == "qlrf_bg":
        return compute_bg_QLRF(config)
    elif alg == "qnlrf":
        return compute_bms_NLRF(config)
    else:
        raise Exception("ERROR: Algorithm (" + alg + ") not found.")


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
    Nvars = int(dim / 2)
    response = Result()

    shifter = 0
    if "different_template" in data and data["different_template"]:
        shifter = Nvars + 1
    # farkas Variables
    rfvars = {}
    # farkas constraints
    farkas_constraints = []
    # rfs coefficients (result)
    rfs = {}
    tr_rfs = {}
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
        # f_s - f_t >= 1
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons + 1
        lambdas2 = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons + 1
        farkas_constraints += farkas.LRF(tr["tr_polyhedron"],
                                         [lambdas, lambdas2],
                                         rf_s, rf_t)

    poly = C_Polyhedron(Constraint_System(farkas_constraints))
    point = poly.get_point()

    if point is None:
        response.set_response(found=False,
                              info="Farkas Polyhedron is empty.")
        return response

    for node in rfvars:
        rfs[node] = ([point.coefficient(c) for c in rfvars[node][1::]],
                     point.coefficient(rfvars[node][0]))
    for tr in transitions:
        tr_rfs[tr["name"]] = {
            tr["source"]: [rfs[tr["source"]]],
            tr["target"]: [rfs[tr["target"]]]
        }

    response.set_response(found=True,
                          rfs=rfs,
                          tr_rfs=tr_rfs,
                          pending_trs=[])
    return response


def LexicographicRF(data):
    response = Result()
    transitions = data["transitions"]

    rfs = {}
    tr_rfs = {}
    no_ranked_trs = transitions
    i = 0
    config = data["inner_alg"].copy()

    while no_ranked_trs:  # while not empty
        i += 1
        config["transitions"] = [tr.copy() for tr in no_ranked_trs]
        result = run(config)
        if result.error():
            return result
        elif not result.found():
            response.set_response(found=False,
                                  info=result.get("info"),
                                  rfs=rfs,
                                  tr_rfs=tr_rfs,
                                  pending_trs=no_ranked_trs)
            return response
        else:
            pending_trs = result.get("pending_trs")
            if False and len(no_ranked_trs) <= len(pending_trs):
                response.set_response(found=False,
                                      info="No decreasing",
                                      rfs=rfs,
                                      tr_rfs=tr_rfs,
                                      pending_trs=no_ranked_trs)
                return response
            res_rfs = result.get("rfs")
            res_tr_rfs = result.get("tr_rfs")
            for node in res_rfs:
                if not(node in rfs):
                    rfs[node] = []
                rfs[node].append(res_rfs[node])
            for tr in res_tr_rfs:
                if not(tr in tr_rfs):
                    tr_rfs[tr] = {}
                for node in res_tr_rfs[tr]:
                    tr_rfs[tr][node].append(res_rfs[tr][node])
            no_ranked_trs = pending_trs

    response.set_response(found=True,
                          rfs=rfs,
                          tr_rfs=tr_rfs,
                          pending_trs=[])
    return response


def BMSRF(data):
    response = Result()
    trans = data["transitions"]

    rfs = {}
    config = data["inner_alg"].copy()
    i = 0
    foundRF = False
    for i in range(len(trans)):
        config["transitions"] = ([trans[i]] +
                                 [trans[j] for j in range(len(trans))
                                  if j != i])

        result = run(config)  # Run NLRF or LRF
        if result.found():
            trfs = result.get("rfs")
            for key in trfs:
                if not(key in rfs):
                    rfs[key] = []
                rfs[key].append(trfs[key])
            new_data = data.copy()
            new_data["transitions"] = result.get("pending_trs")
            if len(result.get("pending_trs")) > 0:
                bmsresult = run(new_data)  # Run BMS
                if bmsresult.found():
                    bms_rfs = bmsresult.get("rfs")
                    # merge rfs
                    for key in bms_rfs:
                        if not(key in rfs):
                            rfs[key] = []
                        rfs[key].append(bms_rfs[key])
                    response.set_response(found=True,
                                          info="Found",
                                          rfs=rfs,
                                          pending_trs=[],
                                          tr_rfs={})

                    return response
                else:
                    return bmsresult
            else:
                response.set_response(found=True,
                                      info="Found",
                                      rfs=rfs,
                                      pending_trs=[])
                return result

    # Impossible to find a BMS
    response.set_response(found=False,
                          info="No BMS",
                          rfs=rfs)
    return response


def compute_adfg_QLRF(data):
    response = Result()
    transitions = data["transitions"]

    dim = _max_dim(transitions)
    Nvars = int(dim / 2)
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
    tr_rfs = {}
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
    # 1.2 - store delta variables
    deltas = {transitions[i]["name"]: Variable(countVar + i)
              for i in range(len(transitions))}
    countVar += len(transitions)
    for tr in transitions:
        rf_s = rfvars[tr["source"]]
        rf_t = rfvars[tr["target"]]
        Mcons = len(tr["tr_polyhedron"].get_constraints())
        # f_s >= 0
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.f(tr["tr_polyhedron"], lambdas,
                                       rf_s, 0)

        # f_s - f_t >= delta[tr]
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.df(tr["tr_polyhedron"], lambdas,
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
    for tr in transitions:
        tr_rfs[tr["name"]] = {
            tr["source"]: [rfs[tr["source"]]],
            tr["target"]: [rfs[tr["target"]]]
        }

    response.set_response(found=True,
                          info="Found",
                          rfs=rfs,
                          tr_rfs=tr_rfs,
                          pending_trs=no_ranked)
    return response


def compute_bg_QLRF(data):
    response = Result()
    transitions = data["transitions"]

    dim = _max_dim(transitions)
    Nvars = int(dim / 2)
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
    tr_rfs = {}
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

    for tr in transitions:
        rf_s = rfvars[tr["source"]]
        rf_t = rfvars[tr["target"]]
        Mcons = len(tr["tr_polyhedron"].get_constraints())
        # f_s >= 0
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.f(tr["tr_polyhedron"], lambdas,
                                       rf_s, 0)

        # f_s - f_t >= 0
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.df(tr["tr_polyhedron"], lambdas,
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
            tr_rfs[tr["name"]] = {
                tr["source"]: [rfs[tr["source"]]],
                tr["target"]: [rfs[tr["target"]]]
            }

        response.set_response(found=True,
                              info="found",
                              rfs=rfs,
                              tr_rfs=tr_rfs,
                              pending_trs=no_ranked)
        return response
    response.set_response(found=False,
                          info="rf found was the trivial")
    return response


def compute_bms_NLRF(data):
    """
    Assuming first transition as main
    transition 0 of data["transitions"] is
    the transition where we look for NLRF
    """
    response = Result()
    transitions = data["transitions"][1::]
    tr = data["transitions"][0]
    max_d = data["algorithm"]["max_depth"] + 1
    min_d = data["algorithm"]["min_depth"]

    for d in range(min_d, max_d):
        OM.printif(2, "d = ", d)
        # 0 - create variables
        dim = _max_dim(data["transitions"])
        Nvars = int(dim / 2)
        shifter = 0
        size_rfs = 0
        if data["different_template"]:
            shifter = (Nvars + 1) * (d)
        # 0.1 - farkas Variables
        rfvars = {}
        deltas = []
        # 0.2 - farkas constraints
        farkas_constraints = []
        # 0.3 - return objects
        rfs = {}  # rfs coefficients (result)
        tr_rfs = {}
        no_ranked = []  # transitions sets no ranked by rfs
        # 0.4 - other stuff
        nodeList = {}
        countVar = 0

        # 1 - init variables
        # 1.1 - store rfs variables
        if not(tr["source"] in nodeList):
            f = [[Variable(i)
                  for i in range(countVar + (Nvars + 1) * di,
                                 countVar + (Nvars + 1) * (di + 1))]
                 for di in range(d)]
            rfvars[tr["source"]] = f
            countVar += shifter
        if not(tr["target"] in nodeList):
            f = [[Variable(i)
                  for i in range(countVar + (Nvars + 1) * di,
                                 countVar + (Nvars + 1) * (di + 1))]
                 for di in range(d)]
            rfvars[tr["target"]] = f
            countVar += shifter
        countVar += (Nvars + 1) * d
        size_rfs = countVar
        # 1.2 - calculate farkas constraints

        rf_s = rfvars[tr["source"]]
        rf_t = rfvars[tr["target"]]
        Mcons = len(tr["tr_polyhedron"].get_constraints())

        lambdas = [[Variable(countVar + k + Mcons * di)
                    for k in range(Mcons)]
                   for di in range(d + 1)]
        countVar += Mcons * (d + 1)
        # 1.2.3 - NLRF for tr
        farkas_constraints += farkas.NLRF(tr["tr_polyhedron"], lambdas,
                                          rf_s, rf_t)
        # 1.2.4 - df >= 0 for each tri != tr
        for tr2 in transitions:
            if tr == tr2:
                continue
            Mcons2 = len(tr2["tr_polyhedron"].get_constraints())
            for di in range(d):
                lambdas = [Variable(countVar + k) for k in range(Mcons2)]
                farkas_constraints += farkas.df(tr2["tr_polyhedron"],
                                                lambdas,
                                                rf_s[di], rf_t[di], 0)
                countVar += Mcons2

        # 2 - Polyhedron
        poly = C_Polyhedron(Constraint_System(farkas_constraints))
        point = poly.get_point()
        if point is None:
            continue  # not found, try with next d

        for node in rfvars:
            rfs[node] = [([point.coefficient(c)
                           for c in rfvars[node][di][1::]],
                          point.coefficient(rfvars[node][di][0]))
                         for di in range(d)]
        for tr in transitions:
            tr_rfs[tr["name"]] = {
                tr["source"]: [rfs[tr["source"]]],
                tr["target"]: [rfs[tr["target"]]]
            }

        response.set_response(found=True,
                              info="found",
                              rfs=rfs,
                              tr_rfs=tr_rfs,
                              pending_trs=transitions)
        return response

    response.set_response(found=False,
                          info="Not found: max_d = " + str(max_d-1) + " .")
    return response

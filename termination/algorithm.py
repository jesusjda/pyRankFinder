from genericparser.Cfg import Cfg
from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable
from ppl import point as pplpoint

from . import farkas
from .output import Output_Manager as OM
from .result import Result


def run(algorithm, cfg, different_template=False):
    alg = algorithm['name']
    if alg == "lrf_pr":
        return LinearRF(algorithm, cfg,
                        different_template=different_template)
    elif alg == "qlrf_adfg":
        return compute_adfg_QLRF(algorithm, cfg,
                                 different_template=different_template)
    elif alg == "qlrf_bg":
        return compute_bg_QLRF(algorithm, cfg,
                               different_template=different_template)
    elif alg == "qnlrf":
        return compute_bms_NLRF(algorithm, cfg,
                                different_template=different_template)
    else:
        raise Exception("ERROR: Algorithm (" + alg + ") not found.")


def _max_dim(edges):
    maximum = 0
    for e in edges:
        d = e["tr_polyhedron"].get_dimension()
        if d > maximum:
            maximum = d
    return maximum


def _add_invariant(tr_poly, src_id, cfg):
    src_invariant = cfg.get_node_info(src_id, "invariant")

    Nvars = len(cfg.get_var_name())
    poly = C_Polyhedron(dim=Nvars)
    for c in tr_poly.get_constraints():
        poly.add_constraint(c)
    for c in src_invariant.get_constraints():
        poly.add_constraint(c)
    poly.minimized_constraints()
    return poly


def _get_rf(variables, point):
    """
    Assume variables[0] is the independent term
    the result point has as coord(0) the indep term
    """
    exp = Linear_Expression(0)
    for i in range(len(variables)):
        exp += point.coefficient(variables[i])*Variable(i)
    return pplpoint(exp)


def LinearRF(_, cfg, different_template=False):
    transitions = cfg.get_edges()

    dim = _max_dim(transitions)
    Nvars = int(dim / 2)
    response = Result()

    shifter = 0
    if different_template:
        shifter = Nvars + 1
    # farkas Variables
    rfvars = {}
    # farkas constraints
    farkas_constraints = []
    # rfs coefficients (result)
    rfs = {}
    tr_rfs = {}
    # other stuff
    countVar = 0
    for tr in transitions:
        if not(tr["source"] in rfvars):
            f = [Variable(i)
                 for i in range(countVar, countVar + Nvars + 1)]
            rfvars[tr["source"]] = f
            countVar += shifter
        if not(tr["target"] in rfvars):
            f = [Variable(i)
                 for i in range(countVar, countVar + Nvars + 1)]
            rfvars[tr["target"]] = f
            countVar += shifter
    if shifter == 0:
        countVar += Nvars + 1

    for tr in transitions:
        rf_s = rfvars[tr["source"]]
        rf_t = rfvars[tr["target"]]
        poly = _add_invariant(tr["tr_polyhedron"], tr["source"], cfg)
        Mcons = len(poly.get_constraints())

        # f_s >= 0
        # f_s - f_t >= 1
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons + 1
        lambdas2 = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons + 1
        farkas_constraints += farkas.LRF(poly,
                                         [lambdas, lambdas2],
                                         rf_s, rf_t)

    farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
    point = farkas_poly.get_point()

    if point is None:
        response.set_response(found=False,
                              info="Farkas Polyhedron is empty.")
        return response

    for node in rfvars:
        rfs[node] = _get_rf(rfvars[node], point)

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


def LexicographicRF(algorithm, cfg, different_template=False):
    response = Result()
    transitions = cfg.get_edges()

    rfs = {}
    tr_rfs = {}
    no_ranked_trs = transitions
    i = 0
    inner_alg = algorithm["inner_alg"]

    while no_ranked_trs:  # while not empty
        i += 1
        trs = [tr.copy() for tr in no_ranked_trs]
        inner_cfg = Cfg(trs, cfg.get_var_name(),
                        nodes_info=cfg.get_node_info(),
                        init_node=cfg.get_init_node())
        result = run(inner_alg, inner_cfg, different_template)
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


def BMSRF(algorithm, cfg, different_template=False):
    response = Result()

    rfs = {}
    inner_alg = algorithm["inner_alg"]

    result = run(inner_alg, cfg,
                 different_template=different_template)  # Run NLRF or LRF

    if result.found():
        trfs = result.get("rfs")
        for key in trfs:
            if not(key in rfs):
                rfs[key] = []
            rfs[key].append(trfs[key])

        no_ranked_trs = result.get("pending_trs")
        trs = [tr.copy() for tr in no_ranked_trs]

        if len(trs) > 0:
            inner_cfg = Cfg(trs, cfg.get_var_name(),
                            nodes_info=cfg.get_node_info(),
                            init_node=cfg.get_init_node())
            # Run BMS
            bmsresult = run(algorithm, inner_cfg,
                            different_template=different_template)
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
                          rfs=rfs,
                          pending_trs=result.get("pending_trs"))
    return response


def compute_adfg_QLRF(_, cfg, different_template=False):
    response = Result()
    transitions = cfg.get_edges()

    dim = _max_dim(transitions)
    Nvars = int(dim / 2)
    shifter = 0
    if different_template:
        shifter = Nvars + 1
    # farkas Variables
    rfvars = {}
    # farkas constraints
    farkas_constraints = []
    # return objects
    rfs = {}  # rfs coefficients (result)
    tr_rfs = {}
    no_ranked = []  # transitions sets no ranked by rfs
    # other stuff
    countVar = 0
    # 1.1 - store rfs variables
    for tr in transitions:
        if not(tr["source"] in rfvars):
            f = [Variable(i)
                 for i in range(countVar, countVar + Nvars + 1)]
            rfvars[tr["source"]] = f
            countVar += shifter
        if not(tr["target"] in rfvars):
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
        poly = _add_invariant(tr["tr_polyhedron"], tr["source"], cfg)

        Mcons = len(poly.get_constraints())
        # f_s >= 0
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.f(poly, lambdas,
                                       rf_s, 0)

        # f_s - f_t >= delta[tr]
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.df(poly, lambdas,
                                        rf_s, rf_t, deltas[tr["name"]])
        # 0 <= delta[tr] <= 1
        farkas_constraints += [0 <= deltas[tr["name"]],
                               deltas[tr["name"]] <= 1]

    farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
    exp = sum([deltas[tr] for tr in deltas])
    result = farkas_poly.maximize(exp)
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
        rfs[node] = _get_rf(rfvars[node], point)

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


def compute_bg_QLRF(_, cfg, different_template=False):
    response = Result()
    transitions = cfg.get_edges()

    dim = _max_dim(transitions)
    Nvars = int(dim / 2)
    shifter = 0
    if different_template:
        shifter = Nvars + 1
    # farkas Variables
    rfvars = {}
    # farkas constraints
    farkas_constraints = []
    # return objects
    rfs = {}  # rfs coefficients (result)
    tr_rfs = {}
    no_ranked = []  # transitions sets no ranked by rfs
    freeConsts = []
    # other stuff
    countVar = 0
    # 1.1 - store rfs variables
    for tr in transitions:
        if not(tr["source"] in rfvars):
            if not(countVar in freeConsts):
                freeConsts.append(countVar)
            f = [Variable(i)
                 for i in range(countVar, countVar + Nvars + 1)]
            rfvars[tr["source"]] = f
            countVar += shifter
        if not(tr["target"] in rfvars):
            if not(countVar in freeConsts):
                freeConsts.append(countVar)
            f = [Variable(i)
                 for i in range(countVar, countVar + Nvars + 1)]
            rfvars[tr["target"]] = f
            countVar += shifter
    if shifter == 0:
        countVar += Nvars + 1
    size_rfs = countVar

    for tr in transitions:
        rf_s = rfvars[tr["source"]]
        rf_t = rfvars[tr["target"]]
        poly = _add_invariant(tr["tr_polyhedron"], tr["source"], cfg)
        Mcons = len(poly.get_constraints())
        # f_s >= 0
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.f(poly, lambdas,
                                       rf_s, 0)

        # f_s - f_t >= 0
        lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
        countVar += Mcons
        farkas_constraints += farkas.df(poly, lambdas,
                                        rf_s, rf_t, 0)
    farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
    variables = [v for v in range(size_rfs) if not(v in freeConsts)]
    variables += freeConsts
    point = farkas_poly.get_relative_interior_point(variables)
    if point is None:
        response.set_response(found=False,
                              info="No relative interior point")
        return response
    for node in rfvars:
        rfs[node] = _get_rf(rfvars[node], point)
    # check if rfs are non-trivial
    nonTrivial = False
    dfs = {}
    for tr in transitions:
        rf_s = rfs[tr["source"]]
        rf_t = rfs[tr["target"]]
        poly = _add_invariant(tr["tr_polyhedron"], tr["source"], cfg)
        df = Linear_Expression(0)
        constant = rf_s.coefficient(Variable(0)) - rf_t.coefficient(Variable(0))
        for i in range(Nvars):
            df += Variable(i) * rf_s.coefficient(Variable(i+1))
            df -= Variable(Nvars + i) * rf_t.coefficient(Variable(i+1))
        dfs[tr["name"]] = df+constant
        if not nonTrivial:
            answ = poly.maximize(df)
            if(not answ["bounded"] or
               answ["sup_n"] > -constant):
                nonTrivial = True

    if nonTrivial:
        no_ranked = []
        for tr in transitions:
            poly = tr["tr_polyhedron"]
            cons = poly.get_constraints()
            cons.insert(dfs[tr["name"]] == 0)
            newpoly = C_Polyhedron(cons)
            if not newpoly.is_empty():
                tr["tr_polyhedron"] = newpoly
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


def compute_bms_NLRF(algorithm, cfg, different_template=False):
    response = Result()
    all_transitions = cfg.get_edges()

    max_d = algorithm["max_depth"] + 1
    min_d = algorithm["min_depth"]
    dim = _max_dim(all_transitions)
    Nvars = int(dim / 2)

    for tr_idx in range(len(all_transitions)):
        main_tr = all_transitions[tr_idx]
        transitions = [all_transitions[j] for j in range(len(all_transitions))
                       if j != tr_idx]
        OM.printif(2, "trying with : " + main_tr["name"])
        for d in range(min_d, max_d):
            OM.printif(2, "\td = ", d)
            # 0 - create variables
            shifter = 0
            if different_template:
                shifter = (Nvars + 1) * (d)
            # 0.1 - farkas Variables
            rfvars = {}
            # 0.2 - farkas constraints
            farkas_constraints = []
            # 0.3 - return objects
            rfs = {}  # rfs coefficients (result)
            tr_rfs = {}
            # 0.4 - other stuff
            countVar = 0

            # 1 - init variables
            # 1.1 - store rfs variables
            for tr in all_transitions:
                if not(tr["source"] in rfvars):
                    f = [[Variable(i)
                          for i in range(countVar + (Nvars + 1) * di,
                                         countVar + (Nvars + 1) * (di + 1))]
                         for di in range(d)]
                    rfvars[tr["source"]] = f
                    countVar += shifter
                if not(tr["target"] in rfvars):
                    f = [[Variable(i)
                          for i in range(countVar + (Nvars + 1) * di,
                                         countVar + (Nvars + 1) * (di + 1))]
                         for di in range(d)]
                    rfvars[tr["target"]] = f
                    countVar += shifter
            if shifter == 0:
                countVar += (Nvars + 1) * d
            # 1.2 - calculate farkas constraints
            rf_s = rfvars[main_tr["source"]]
            rf_t = rfvars[main_tr["target"]]
            poly = _add_invariant(main_tr["tr_polyhedron"],
                                  main_tr["source"], cfg)
            Mcons = len(poly.get_constraints())

            lambdas = [[Variable(countVar + k + Mcons * di)
                        for k in range(Mcons)]
                       for di in range(d + 1)]
            countVar += Mcons * (d + 1)
            # 1.2.3 - NLRF for tr
            farkas_constraints += farkas.NLRF(poly, lambdas,
                                              rf_s, rf_t)
            # 1.2.4 - df >= 0 for each tri != tr
            for tr2 in transitions:
                Mcons2 = len(tr2["tr_polyhedron"].get_constraints())
                rf_s2 = rfvars[tr2["source"]]
                rf_t2 = rfvars[tr2["target"]]
                for di in range(d):
                    lambdas = [Variable(countVar + k) for k in range(Mcons2)]
                    farkas_constraints += farkas.df(tr2["tr_polyhedron"],
                                                    lambdas,
                                                    rf_s2[di], rf_t2[di], 0)
                    countVar += Mcons2

            # 2 - Polyhedron
            farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
            point = farkas_poly.get_point()
            if point is None:
                continue  # not found, try with next d

            for node in rfvars:
                rfs[node] = [_get_rf(rfvars[node][di], point)
                             for di in range(d)]
            for tr2 in all_transitions:
                if(tr2["source"] in [main_tr["source"], main_tr["target"]] and
                   tr2["target"] in [main_tr["source"], main_tr["target"]]):
                    tr_rfs[tr2["name"]] = {
                        tr2["source"]: [rfs[tr2["source"]]],
                        tr2["target"]: [rfs[tr2["target"]]]
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

from termination import Output_Manager as OM
from lpi import C_Polyhedron
from genericparser import constants as gconsts
from termination import constants as consts


def cfrprops_options():
    return [consts.cfr.properties.user, consts.cfr.properties.cone, consts.cfr.properties.head,
            consts.cfr.properties.call, consts.cfr.properties.head_var, consts.cfr.properties.call_var,
            consts.cfr.properties.john, consts.cfr.properties.split]


def compute_cfrprops(cfg, only_nodes=None, modes=[], invariant_type="none"):
    if len(modes) == 0:
        return {}
    if only_nodes is not None and len(only_nodes) == 0:
        return {}
    do_head_props = consts.cfr.properties.head in modes
    do_head_var_props = consts.cfr.properties.head_var in modes
    do_call_props = consts.cfr.properties.call in modes
    do_call_var_props = consts.cfr.properties.call_var in modes
    do_user_props = consts.cfr.properties.user in modes
    do_cone_props = consts.cfr.properties.cone in modes
    split = consts.cfr.properties.split in modes
    for t in cfg.get_edges():
        cfr_poly = t[gconsts.transition.polyhedron].copy()
        if invariant_type != "none":
            try:
                invariants = [c for c in cfg.nodes[t["source"]]["invariant_" + str(invariant_type)].get_constraints()]
            except Exception:
                invariants = []
            cfr_poly.add_constraints(invariants)
        t[gconsts.transition.cfr_polyhedron] = cfr_poly
    c_props, usr_props, au_props = {}, {}, {}
    if do_cone_props:
        c_props = cone_properties(cfg, only_nodes)
        cfg.set_nodes_info(c_props, consts.cfr.properties.cone)
    if do_user_props:
        usr_props = user_properties(cfg, only_nodes)
    if do_head_props or do_head_var_props or do_call_props or do_call_var_props:
        au_props = project_props(cfg, only_nodes,
                                 do_head_props=do_head_props,
                                 do_head_var_props=do_head_var_props,
                                 do_call_props=do_call_props,
                                 do_call_var_props=do_call_var_props)
        cfg.set_nodes_info(au_props, consts.cfr.properties.project)
    # SAVE PROPS
    final_props = merge_dicts([au_props, c_props, usr_props])
    if split:
        for n in final_props:
            props = []
            for ps in final_props[n]:
                props += [[p] for p in ps if [p] not in props]
            final_props[n] = props
    return final_props


def project_props(cfg, only_nodes=None, do_head_props=False, do_head_var_props=False, do_call_props=False, do_call_var_props=False):
    global_vars = cfg.get_info(gconsts.variables)
    N = int(len(global_vars) / 2)
    vs = global_vars[:N]
    pvs = global_vars[N:2 * N]
    polys_props = {n: [] for n in cfg.get_nodes() if only_nodes is None or n in only_nodes}
    for t in cfg.get_edges():
        poly = t[gconsts.transition.polyhedron]
        if only_nodes is None or t["source"] in only_nodes:
            if do_head_props:
                polys_props[t["source"]].append(poly.project(vs))
            if do_head_var_props:
                for v in vs:
                    polys_props[t["source"]].append(poly.project(v))
        if only_nodes is None or t["target"] in only_nodes:
            if do_call_props or do_call_var_props:
                vars_ = pvs + vs + t[gconsts.transition.localvariables]
                p = C_Polyhedron(constraints=poly.get_constraints(vars_), variables=vars_)
            if do_call_props:
                polys_props[t["target"]].append(p.project(vs))
            if do_call_var_props:
                for v in vs:
                    polys_props[t["target"]].append(p.project(v))
    au_props = {}
    for node in polys_props:
        polys = polys_props[node]
        props = []
        for p in polys:
            cs = p.get_constraints()
            if len(cs) > 0:
                props.append(cs)
        if len(props) > 0:
            au_props[node] = props
    return au_props


def user_properties(cfg, nodes_to_refine=None):
    node_data = cfg.get_nodes(data=True)

    usr_props = {}
    for node, data in node_data:
        if nodes_to_refine is not None and node not in nodes_to_refine:
            continue
        n_props = [p for p in data.get(gconsts.node.cfrproperties, [])]
        if len(n_props) > 0:
            usr_props[node] = n_props
    return usr_props


def cone_properties(cfg, nodes_to_refine=None):
    from ppl import Variable
    from lpi import Expression
    from termination import farkas
    from termination.algorithm.utils import get_free_name
    global_vars = cfg.get_info(gconsts.variables)
    Nvars = int(len(global_vars) / 2)
    cone_props = {}
    OM.printif(2, "Positive functions of the cone as properties of CFR")
    for node in cfg.get_nodes():
        n_props = []
        if nodes_to_refine is not None and node not in nodes_to_refine:
            continue
        for t in cfg.get_edges(source=node):
            t_props = []
            tr_poly = t[gconsts.transition.cfr_polyhedron].copy()
            tr_poly = tr_poly.project(global_vars[:Nvars])
            if tr_poly.is_empty():
                continue
            Mcons = len(tr_poly.get_constraints())
            taken_vars = []
            f = get_free_name(taken_vars, name="a_", num=Nvars + 1)
            taken_vars += f
            lambdas = get_free_name(taken_vars, name="l", num=Mcons)
            taken_vars += lambdas
            farkas_constraints = farkas.farkas(tr_poly, [Expression(v) for v in lambdas],
                                               [Expression(v) for v in f[1:]], Expression(f[0]))
            farkas_poly = C_Polyhedron(constraints=farkas_constraints, variables=taken_vars)
            generators = farkas_poly.get_generators()
            OM.printif(3, generators)
            for g in generators:
                if not g.is_ray():
                    continue
                exp = Expression(g.coefficient(Variable(0)))
                is_constant = True
                for i in range(Nvars):
                    coef = g.coefficient(Variable(i + 1))
                    if coef != 0:
                        is_constant = False
                    exp += Expression(coef) * Expression(global_vars[i])
                if not is_constant:
                    t_props.append(exp >= Expression(0))

            if len(t_props) > 0:
                n_props.append(t_props)

        if len(n_props) > 0:
            OM.printif(2, "Node \"{}\", Adding props {}".format(node, str(n_props)))
            cone_props[node] = n_props
    return cone_props


def lattice(l):
    s = [[]]
    for e in l:
        ns = []
        for ps in s:
            nps = ps[:]
            nps.append(e)
            ns.append(nps)
        s = s + ns
    return s[1:]


def merge_dicts(list_dict):
    res = {}
    for di in list_dict:
        for k in di:
            if k not in res:
                res[k] = []
            res[k] += di[k]
    return res

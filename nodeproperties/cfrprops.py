from termination import Output_Manager as OM

def cfrprops_options():
    return ["cfr_user_properties", "cfr_cone_properties", "cfr_head_properties",
            "cfr_call_properties", "cfr_head_var_properties", "cfr_call_var_properties"]

def compute_cfrprops(cfg, only_nodes=None, props=[], invariant_type="none"):
    if len(props) == 0:
        return {}
    if only_nodes is not None and len(only_nodes) == 0:
        return {}
    do_head_props="cfr_head_properties" in props
    do_head_var_props="cfr_head_var_properties" in props
    do_call_props="cfr_call_properties" in props
    do_call_var_props="cfr_call_var_properties" in props
    do_user_props="cfr_user_properties" in props
    do_cone_props="cfr_cone_properties" in props
    from lpi.Lazy_Polyhedron import C_Polyhedron
    from ppl import Constraint_System
    global_vars = cfg.get_info("global_vars")
    for t in cfg.get_edges():
        all_vars = global_vars + t["local_vars"]
        ppl_cons = [c.transform(all_vars, lib="ppl")
                        for c in t["constraints"] if c.is_linear()]
        if invariant_type != "none":
            try:
                invariants = [c for c in cfg.nodes[t["source"]]["invariant_"+str(invariant_type)].get_constraints()]
            except Exception:
                invariants = []
            ppl_cons += invariants
        t["cfr_polyhedron"] = C_Polyhedron(Constraint_System(ppl_cons), dim=len(all_vars))
    c_props, usr_props, au_props = {}, {}, {}
    if do_cone_props:
        c_props = cone_properties(cfg, only_nodes)
        cfg.set_nodes_info(c_props, "cfr_cone_properties")
    if do_user_props:
        usr_props = user_properties(cfg, only_nodes)
    if do_head_props or do_head_var_props or do_call_props or do_call_var_props:
        au_props = project_props(cfg, only_nodes, do_head_props=do_head_props, do_head_var_props=do_head_var_props, do_call_props=do_call_props, do_call_var_props=do_call_var_props)
        cfg.set_nodes_info(au_props, "cfr_project_properties")
    # SAVE PROPS
    final_props = merge_dicts([au_props,c_props,usr_props])
    return final_props


def project_props(cfg, only_nodes, do_head_props, do_head_var_props, do_call_props, do_call_var_props):
    global_vars = cfg.get_info("global_vars")
    N = int(len(global_vars)/2)
    idx_vs = [i for i in range(N)]
    idx_pvs = [i for i in range(N,2*N)]
    polys_props = {n:[] for n in cfg.get_nodes() if only_nodes is None or n in only_nodes}
    for t in cfg.get_edges():
        poly = t["cfr_polyhedron"]
        if only_nodes is None or t["source"] in only_nodes:
            if do_head_props:
                polys_props[t["source"]].append(poly.project(idx_vs))
            if do_head_var_props:
                for i in idx_vs:
                    polys_props[t["source"]].append(poly.project(i))
        if only_nodes is None or t["target"] in only_nodes:
            if do_call_props:
                polys_props[t["target"]].append(poly.project(idx_pvs))
            if do_call_var_props:
                for i in idx_pvs:
                    polys_props[t["target"]].append(poly.project(i))
    au_props = {}
    from ppl import Variable
    from genericparser.expressions import ExprTerm
    for node in polys_props:
        polys = polys_props[node]
        # Remove duplicated
        i, j = 0, 1
        while i < len(polys):
            j = i + 1
            while j < len(polys):
                if i == j:
                    j += 1
                    continue
                if polys[i] == polys[j]:
                    del polys[j]
                    j -= 1
                j+=1
            i+=1
        props = []
        for p in polys:
            cs = p.get_constraints()
            own_cs = []
            for c in cs:
                exp = ExprTerm(c.inhomogeneous_term())
                is_constant = True
                for i in range(c.space_dimension()):
                    coef = c.coefficient(Variable(i))
                    if coef != 0:
                        is_constant = False
                        exp += ExprTerm(coef)*ExprTerm(global_vars[i])
                if not is_constant:
                    if not c.is_equality():
                        own_cs.append(exp >= ExprTerm(0))
                    elif do_call_var_props or do_head_var_props or True:
                        own_cs.append(exp == ExprTerm(0))
            if len(own_cs) > 0:
                #props += lattice(own_cs)
                props.append(own_cs)
        if len(props) > 0:
            au_props[node] = props
    return au_props

def user_properties(cfg, nodes_to_refine):
    node_data = cfg.get_nodes(data=True)

    usr_props = {}
    for node, data in node_data:
        if nodes_to_refine is not None and node not in nodes_to_refine:
            continue
        if "cfr_properties" in data:
            n_props = [p for p in data["cfr_properties"]]
            if len(n_props) > 0:
                usr_props[node] = n_props
    return usr_props

def cone_properties(cfg, nodes_to_refine):
    from ppl import Constraint_System
    from ppl import Variable
    from genericparser.expressions import ExprTerm
    from lpi import C_Polyhedron
    from termination import farkas
    global_vars = cfg.get_info("global_vars")
    Nvars = int(len(global_vars) / 2)
    cone_props = {}
    OM.printif(2, "Positive functions of the cone as properties of CFR")
    for node in cfg.get_nodes():
        n_props = []
        if nodes_to_refine is not None and node not in nodes_to_refine:
            continue
        for t in cfg.get_edges(source=node):
            t_props = []
            from copy import deepcopy
            tr_poly = deepcopy(t["cfr_polyhedron"])
            # PROJECT TO VARS
            from ppl import Variables_Set
            var_set = Variables_Set()
            # (prime and local variables)
            for i in range(Nvars, tr_poly.get_dimension()):  # Vars from n to m-1 inclusive
                var_set.insert(Variable(i))
            tr_poly.remove_dimensions(var_set)
            if tr_poly.is_empty():
                continue
            Mcons = len(tr_poly.get_constraints())
            f = [Variable(i) for i in range(1, Nvars + 1)]
            countVar = Nvars + 1
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            farkas_constraints = farkas.farkas(tr_poly, lambdas, f, Variable(0))
            farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
            generators = farkas_poly.get_generators()
            OM.printif(3, generators)
            for g in generators:
                if not g.is_ray():
                    continue
                exp = ExprTerm(g.coefficient(Variable(0)))
                is_constant = True
                for i in range(Nvars):
                    coef = g.coefficient(Variable(i+1))
                    if coef != 0:
                        is_constant = False
                    exp += ExprTerm(coef)*ExprTerm(global_vars[i])
                if not is_constant:
                    t_props.append(exp >= ExprTerm(0))

            if len(t_props) > 0:
                #n_props += lattice(t_props)
                n_props += [[p] for p in t_props]
                #n_props.append(t_props)

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
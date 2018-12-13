import os
from termination.output import Output_Manager as OM
from subprocess import PIPE
from subprocess import Popen
    
__all__ = ['partialevaluate', 'control_flow_refinement','prepare_scc']

def prepare_scc(cfg, scc, invariant_type):
    scc_edges = scc.get_edges()
    scc_copy = scc.edge_data_subgraph(scc_edges)
    nodes = scc.get_nodes()
    init_node = "scc_init"
    it = 0
    while init_node in nodes:
        it += 1
        init_node = "scc_init_"+str(it)
    from lpi.Lazy_Polyhedron import C_Polyhedron
    inv_name = "invariant_"+str(invariant_type)
    Nvars = len(cfg.get_info("global_vars"))
    t_names = [e["name"] for e in scc_edges]
    it = 0
    from copy import deepcopy
    for entry in nodes:
        for t in cfg.get_edges(target=entry):
            name = t["name"]
            if name in t_names:
                continue
            src = t["source"]
            new_t = deepcopy(t)
            new_t["source"] = init_node
            name = "tr"+str(it)
            it += 1
            while name in t_names:
                name = "tr"+str(it)
                it += 1
            new_t["name"] = name
            Nlocal_vars = len(t["local_vars"])
            tr_cons = t["tr_polyhedron"].get_constraints()
            try:
                inv = cfg.nodes[src][inv_name].get_constraints()
            except:
                inv = []
            tr_poly = C_Polyhedron(dim=Nvars+Nlocal_vars)
            for c in tr_cons:
                tr_poly.add_constraint(c)
            for c in inv:
                tr_poly.add_constraint(c)
            new_t["polyhedron"] = tr_poly
            scc_copy.add_edge(**new_t)
    scc_copy.set_nodes_info({init_node:C_Polyhedron(dim=int(Nvars/2))},inv_name)
    scc_copy.set_info("init_node",init_node)
    scc_copy.set_info("entry_nodes",[init_node])
    return scc_copy

def control_flow_refinement(cfg, config, console=False, writef=False, only_nodes=None, inner_invariants=True):
    from termination.algorithm.utils import showgraph
    from nodeproperties import compute_invariants
    au_prop = config["cfr_automatic_properties"]
    cfr_ite = config["cfr_iterations"]
    cfr_inv = config["cfr_invariants"]
    # cfr_it_st = config["cfr_iteration_strategy"]
    cfr_usr_props = config["cfr_user_properties"]
    cfr_cone_props = config["cfr_cone_properties"] if "cfr_cone_properties" in config else False
    cfr_inv_thre = config["cfr_invariants_threshold"]
    tmpdir = config["tmpdir"]
    pe_cfg = cfg
    sufix = ""
    for it in range(0, cfr_ite):
        if inner_invariants:
            compute_invariants(pe_cfg, abstract_domain=cfr_inv, use_threshold=cfr_inv_thre)
        pe_cfg.remove_unsat_edges()
        showgraph(pe_cfg, config, sufix=sufix, invariant_type=cfr_inv, console=console, writef=writef)
        pe_cfg = partialevaluate(pe_cfg, auto_props=au_prop, cone_props=cfr_cone_props,
                                 user_props=cfr_usr_props, tmpdir=tmpdir,
                                 invariant_type=cfr_inv, nodes_to_refine=only_nodes)
        sufix="_cfr"+str(it+1)
        if "show_with_invariants" in config and config["show_with_invariants"] and cfr_inv != "none":
            sufix += "_with_inv_"+str(cfr_inv)
    showgraph(pe_cfg, config, sufix=sufix, invariant_type=cfr_inv, console=console, writef=writef)
    return pe_cfg

def partialevaluate(cfg, auto_props=4, user_props=False, tmpdir=None, invariant_type=None, nodes_to_refine=None, cone_props=False):
    if not(auto_props in range(0, 5)):
        raise ValueError("CFR automatic properties mode unknown: {}.".format(auto_props))
    
    if tmpdir is None or tmpdir == "":
        import tempfile
        tmpdirname = tempfile.mkdtemp()
    else:
        tmpdirname = tmpdir
    tmpplfile = os.path.join(tmpdirname, "source.pl")
    cfg.toProlog(path=tmpplfile, invariant_type=invariant_type)
    N = int(len(cfg.get_info("global_vars")) / 2)
    vs = ""
    if N > 0:
        vs = "(_"
        if N > 1:
            vs += ",_"*int(N - 1)
        vs += ")"
    if len(cfg.get_info("entry_nodes")) > 0:
        init_node = cfg.get_info("entry_nodes")[0]
    else:
        init_node = cfg.get_info("init_node")
    initNode = "n_{}{}".format(init_node, vs)
    if OM.verbosity > 2:
        with open(tmpplfile, 'r') as fin:
            OM.printif(3, fin.read())


    # PROPERTIES
    propsfile = set_props(cfg, tmpdirname, tmpplfile, auto_props, user_props, nodes_to_refine, cone_props)

    # PE
    pepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin','pe.sh')
    pipe = Popen([pepath, tmpplfile, initNode, '-s', '-p', (propsfile), '-r', tmpdirname],
                 stdout=PIPE, stderr=PIPE)
    fcpeprogram, err = pipe.communicate()
    if err is not None and err:
            raise Exception(err)

    # Convert to CFG
    from genericparser.Parser_fc import Parser_fc
    pfc = Parser_fc()
    pe_cfg = pfc.parse_string(fcpeprogram.decode("utf-8"))
    rmded = pe_cfg.remove_unsat_edges()
    if len(rmded)> 0:
        OM.printif(1, "Removed edges {} because they where unsat.".format(rmded))
    OM.printif(4, fcpeprogram.decode("utf-8"))
    return pe_cfg
    

def set_props(cfg, tmpdirname, tmpplfile, auto_props, user_props, nodes_to_refine, cone_props):
    if auto_props in range(1,5):
        propspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin','props.sh')
        pipe = Popen([propspath, tmpplfile, '-l', str(auto_props), '-r', tmpdirname],
                     stdout=PIPE, stderr=PIPE)
        propsfile, err = pipe.communicate()
        if err is not None and err:
                raise Exception(err)
        propsfile = propsfile.decode("utf-8")
    else:
        propsfile = os.path.join(tmpdirname, "source_output/source.props")
        basedir = os.path.dirname(propsfile)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        open(propsfile,'a').close()

    gvars = cfg.get_info("global_vars")
    gvars = gvars[:int(len(gvars)/2)]
    pvars = _plVars(len(gvars))
    if cone_props:
        c_props = cone_properties(cfg, nodes_to_refine)
        _add_props(propsfile, c_props, gvars, pvars)
    if user_props:
        node_data = cfg.get_nodes(data=True)

        usr_props = {}
        for node, data in node_data:
            if nodes_to_refine is not None and node not in nodes_to_refine:
                continue
            if "cfr_properties" in data:
                n_props = [p for p in data["cfr_properties"]]
                if len(n_props) > 0:
                    usr_props[node] = n_props
        _add_props(propsfile, usr_props, gvars, pvars)

    if nodes_to_refine is not None and len(nodes_to_refine) > 0:
        nodes = cfg.get_nodes()
        if len(nodes) != len(nodes_to_refine):
            remove_nodes_props(propsfile, list(set(nodes) - set(nodes_to_refine)))

    # SAVE PROPS
    props = _parse_props(propsfile, gvars, pvars)
    cfg.set_nodes_info(props, "cfr_used_properties")
    OM.printif(2, "CFR with props: {}".format(props))
    if OM.verbosity > 2:
        with open(propsfile, "r") as f:
            OM.printif(3, f.read())
    return propsfile

def _do_modifications(props):
    ps = {}
    for n in props:
        ps[n] = props[n]
        break
    return ps


def _parse_props(filename, gvars, pvars):
    correspondance = list(zip(pvars, gvars))
    props = {}
    lines = [line.rstrip('\n') for line in open(filename)]
    for line in lines:
        if not line:
            continue
        endname = line.find("(")
        node_name = line[2:endname]
        begincons = line.find("[", endname)
        endcons = line.find("].",begincons)
        strs_cons = line[begincons+1:endcons].split(",")
        from genericparser import parse_constraint
        cons = [parse_constraint(_translate(c, correspondance)) for c in strs_cons]
        if node_name not in props:
            props[node_name] = []
        props[node_name].append(cons)
    return props


def cone_properties(cfg, nodes_to_refine):
    from ppl import Constraint_System
    from ppl import Variable
    from genericparser.expressions import ExprTerm
    from lpi import C_Polyhedron
    from termination import farkas
    global_vars = cfg.get_info("global_vars")
    Nvars = int(len(global_vars) / 2)
    cone_props = {}
    for node in cfg.get_nodes():
        n_props = []
        if nodes_to_refine is not None and node not in nodes_to_refine:
            continue
        for t in cfg.get_edges(source=node):
            t_props = []
            tr_poly = t["polyhedron"]
            # PROJECT TO VARS
            from ppl import Variables_Set
            var_set = Variables_Set()
            # (prime and local variables)
            for i in range(Nvars, tr_poly.get_dimension()):  # Vars from n to m-1 inclusive
                var_set.insert(Variable(i))
            # tr_poly.remove_dimensions(var_set)
            if tr_poly.is_empty():
                continue
            Mcons = len(tr_poly.get_constraints())
            f = [Variable(i) for i in range(0, Nvars + 1)]
            countVar = Nvars + 1
            lambdas = [Variable(k) for k in range(countVar, countVar + Mcons)]
            farkas_constraints = farkas.f(tr_poly, lambdas, f, 0)
            farkas_poly = C_Polyhedron(Constraint_System(farkas_constraints))
            generators = farkas_poly.get_generators()
            OM.printif(3, generators)
            for g in generators:
                exp = ExprTerm(g.coefficient(Variable(0)))
                is_cero = True
                for i in range(Nvars):
                    coef = g.coefficient(Variable(i+1))
                    if coef != 0:
                        is_cero = False
                    exp += ExprTerm(coef)*ExprTerm(global_vars[i])
                if not is_cero:
                    t_props.append(exp >= ExprTerm(0))
                
            if len(t_props) > 0:
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
                n_props += lattice(t_props)
                #n_props += [[p] for p in t_props]
                #n_props.append(t_props)
        if len(n_props) > 0:
            OM.printif(2, "Node {}: Adding props {}".format(node, str(n_props)))
            cone_props[node] = n_props
    return cone_props

def _add_props(filename, props, gvars, pvars):
    vars_str = ",".join(pvars)
    renamedvars = lambda v: pvars[gvars.index(v)]
    with open(filename, "a") as f:
        for node in props:
            for cons in props[node]:
                cons_str = ", ".join([c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                                      for c in cons])
                line = "n_{}({}) :- [{}].\n".format(node,vars_str, cons_str)
                f.write(line)
        f.write('\n')

def _translate(c, tdict):
    dic = sorted(tdict, key=lambda x: len(x[0]), reverse=True)
    text = c
    for o, d in dic:
        text = text.replace(o, d)
    return text

def _plVars(N):
    from string import ascii_uppercase
    ABC=list(ascii_uppercase)
    lenABC=len(ABC)
    plvars = ABC[:N]
    if N > lenABC:
        plvars += [ABC[i%lenABC]+str(int(i/lenABC)) for i in range(lenABC, N)]
    return plvars

def remove_nodes_props(filename, nodes):
    from shutil import move
    destfile=filename+".tmp"
    ops = tuple([("n_{}(".format(n)) for n in nodes])
    with open(filename, "r") as fin, open(destfile, "w") as fout:
        for line in fin:
            if not line.startswith(ops):
                fout.write(line)
    move(destfile, filename)

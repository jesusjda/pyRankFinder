import os
import re
from termination.output import Output_Manager as OM
from subprocess import PIPE
from subprocess import Popen

__all__ = ['partialevaluate', 'control_flow_refinement', 'prepare_scc']


def control_flow_refinement(cfg, config, console=False, writef=False, only_nodes=None, inner_invariants=True):
    from termination.algorithm.utils import showgraph
    from nodeproperties import compute_invariants
    cfr_ite = config["cfr_iterations"]
    cfr_inv = config["cfr_invariants"]
    cfr_inv_thre = config["cfr_invariants_threshold"]
    # cfr_it_st = config["cfr_iteration_strategy"]
    from nodeproperties.cfrprops import cfrprops_options
    props_methods = []
    for op in cfrprops_options():
        if op in config and config[op]:
            props_methods.append(op)

    tmpdir = config["tmpdir"]
    pe_cfg = cfg
    sufix = ""
    for it in range(0, cfr_ite):
        if inner_invariants:
            compute_invariants(pe_cfg, abstract_domain=cfr_inv, threshold_modes=cfr_inv_thre)
        pe_cfg.remove_unsat_edges()
        showgraph(pe_cfg, config, sufix=sufix, invariant_type=cfr_inv, console=console, writef=writef)
        pe_cfg = partialevaluate(pe_cfg, props_methods=props_methods, tmpdir=tmpdir,
                                 invariant_type=cfr_inv, nodes_to_refine=only_nodes)
        sufix = "_cfr" + str(it + 1)
        if "show_with_invariants" in config and config["show_with_invariants"] and cfr_inv != "none":
            sufix += "_with_inv_" + str(cfr_inv)
    showgraph(pe_cfg, config, sufix=sufix, invariant_type=cfr_inv, console=console, writef=writef)
    return pe_cfg


def partialevaluate(cfg, props_methods=[], tmpdir=None, invariant_type=None, nodes_to_refine=None):
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
            vs += ",_" * int(N - 1)
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
    propsfile = set_props(cfg, tmpdirname, props_methods=props_methods,
                          nodes_to_refine=nodes_to_refine, invariant_type=invariant_type)

    # PE
    pepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', 'pe.sh')
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
    if len(rmded) > 0:
        OM.printif(1, "Removed edges {} because they where unsat.".format(rmded))
    OM.printif(4, fcpeprogram.decode("utf-8"))
    properties_to_copy = ["asserts", "cfr_properties"]
    original_data = {n: v for n, v in cfg.get_nodes(data=True)}
    for p in properties_to_copy:
        p_dict = {}
        new_init = pe_cfg.get_info("init_node")
        if p in original_data[new_init[2:]]:
            p_dict[new_init] = original_data[new_init[2:]][p]
        for pe_node in pe_cfg.get_nodes():
            if pe_node == init_node:
                continue
            orig_node = re.sub("\_\_\_[0-9]+$", "", pe_node[2:])
            if orig_node in original_data:
                if p in original_data[orig_node]:
                    p_dict[pe_node] = original_data[orig_node][p]
        if p_dict:
            OM.printif(2, "WARNING: property {} added to the cfr graph without renaming variables.".format(p))
            pe_cfg.set_nodes_info(p_dict, p)
    return pe_cfg


def set_props(cfg, tmpdirname, props_methods, nodes_to_refine, invariant_type):
    gvars = cfg.get_info("global_vars")
    gvars = gvars[:int(len(gvars) / 2)]
    pvars = _plVars(len(gvars))
    propsfile = os.path.join(tmpdirname, "source_output/source.props")
    basedir = os.path.dirname(propsfile)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    open(propsfile, 'a').close()

    from nodeproperties.cfrprops import compute_cfrprops
    props = compute_cfrprops(cfg, nodes_to_refine, modes=props_methods, invariant_type=invariant_type)
    _add_props(propsfile, props, gvars, pvars)

    # SAVE PROPS
    OM.printif(2, "CFR with props: {}".format(props))
    return propsfile


def _plVars(N):
    from string import ascii_uppercase
    ABC = list(ascii_uppercase)
    lenABC = len(ABC)
    plvars = ABC[:N]
    if N > lenABC:
        plvars += [ABC[i % lenABC] + str(int(i / lenABC)) for i in range(lenABC, N)]
    return plvars


def _add_props(filename, props, gvars, pvars):
    vars_str = ",".join(pvars)
    renamedvars = lambda v: pvars[gvars.index(v)]
    with open(filename, "a") as f:
        for node in props:
            for cons in props[node]:
                cons_str = ", ".join([c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                                      for c in cons])
                line = "n_{}({}) :- [{}].\n".format(node, vars_str, cons_str)
                f.write(line)
        f.write('\n')


def prepare_scc(cfg, scc, invariant_type):
    scc_edges = scc.get_edges()
    scc_copy = scc.edge_data_subgraph(scc_edges)
    nodes = scc.get_nodes()
    init_node = "scc_init"
    it = 0
    while init_node in nodes:
        it += 1
        init_node = "scc_init_" + str(it)
    from lpi import C_Polyhedron
    inv_name = "invariant_" + str(invariant_type)
    gvs = cfg.get_info("global_vars")
    Nvars = len(gvs)
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
            name = "tr" + str(it)
            it += 1
            while name in t_names:
                name = "tr" + str(it)
                it += 1
            new_t["name"] = name
            tr_poly = t["polyhedron"].copy()
            try:
                inv = cfg.nodes[src][inv_name].get_constraints()
            except Exception:
                inv = []
            tr_poly.add_constraints(inv)
            new_t["polyhedron"] = tr_poly
            scc_copy.add_edge(**new_t)
    scc_copy.set_nodes_info({init_node: C_Polyhedron(variables=gvs[:int(Nvars / 2)])}, inv_name)
    scc_copy.set_info("init_node", init_node)
    scc_copy.set_info("entry_nodes", [init_node])
    return scc_copy


#####################################
# OLD METHODS TO COMPUTE PROPERTIES #
#####################################

def johns_props(cfg, auto_props, tmpplfile, tmpdirname):
    gvars = cfg.get_info("global_vars")
    gvars = gvars[:int(len(gvars) / 2)]
    pvars = _plVars(len(gvars))
    if auto_props in range(1, 5):
        propspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', 'props.sh')
        pipe = Popen([propspath, tmpplfile, '-l', str(auto_props), '-r', tmpdirname],
                     stdout=PIPE, stderr=PIPE)
        propsfile, err = pipe.communicate()
        if err is not None and err:
                raise Exception(err)
        propsfile = propsfile.decode("utf-8")
        au_props = _parse_props(propsfile, gvars, pvars)
        cfg.set_nodes_info(au_props, "cfr_auto_properties")
        return au_props
    return {}


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
        endcons = line.find("].", begincons)
        strs_cons = line[begincons + 1:endcons].split(",")
        from genericparser import parse_constraint
        cons = [parse_constraint(_translate(c, correspondance)) for c in strs_cons]
        if node_name not in props:
            props[node_name] = []
        props[node_name].append(cons)
    return props


def remove_nodes_props(filename, nodes):
    from shutil import move
    destfile = filename + ".tmp"
    ops = tuple([("n_{}(".format(n)) for n in nodes])
    with open(filename, "r") as fin, open(destfile, "w") as fout:
        for line in fin:
            if not line.startswith(ops):
                fout.write(line)
    move(destfile, filename)


def _translate(c, tdict):
    dic = sorted(tdict, key=lambda x: len(x[0]), reverse=True)
    text = c
    for o, d in dic:
        text = text.replace(o, d)
    return text

import os
import re
from termination.output import Output_Manager as OM
from subprocess import PIPE
from subprocess import Popen

__all__ = ['partialevaluate', 'control_flow_refinement', 'prepare_scc']


def control_flow_refinement(cfg, config, console=False, writef=False, only_nodes=None):
    from termination.algorithm.utils import showgraph
    from nodeproperties import invariant
    if len(cfg.get_info("global_vars")) == 0:
        OM.printif(1, "CFR is not applied because there is no variables")
        return cfg
    cfr_ite = config["cfr_iterations"]
    cfr_inv = config["cfr_invariants"]
    cfr_inv_type = config["invariants"] if cfr_inv else "none"
    cfr_nodes_mode = config["cfr_nodes_mode"]
    cfr_nodes = config["cfr_nodes"]
    OM.printseparator(1)
    OM.printif(1, "CFR({})".format(cfr_ite))
    from nodeproperties.cfrprops import cfrprops_options
    props_methods = [op for op in cfrprops_options() if config.get(op, False)]

    tmpdir = config["tmpdir"]

    def get_nodes_to_refine(cfg, mode, cfr_nodes, o_nodes):
        only_john, nodes_to_refine = False, only_nodes
        if mode == "john":
            only_john = True
        elif mode != "all":
            if mode == "cyclecutnodes":
                cfr_nodes = cfg.cycle_cut_nodes()
            if o_nodes is None:
                nodes_to_refine = cfr_nodes
            else:
                nodes_to_refine = [n for n in o_nodes if n in cfr_nodes]
        if nodes_to_refine is not None:
            nodes_to_refine = cfg.get_corresponding_nodes_list(nodes_to_refine)
        return only_john, nodes_to_refine

    def summary(token, g):
        nodes = len(g.get_nodes())
        trs = len(g.get_edges())
        sccs = len([1 for scc in g.get_strongly_connected_component() if len(scc.get_edges()) > 0])
        return "{}:\n- nodes: {}\n- trs: {}\n- sccs: {} (with 1 or more trs)".format(token, nodes, trs, sccs)
    OM.lazy_printif(1, lambda: summary("Original", cfg))
    pe_cfg = cfg
    sufix = ""
    for it in range(0, cfr_ite):
        if cfr_inv and it > 0:
            invariant.compute_invariants(pe_cfg)
        pe_cfg.remove_unsat_edges()
        only_john, nodes_to_refine = get_nodes_to_refine(pe_cfg, cfr_nodes_mode, cfr_nodes, only_nodes)
        showgraph(pe_cfg, config, sufix=sufix, invariant_type=cfr_inv_type, console=console, writef=writef)
        pe_cfg = partialevaluate(pe_cfg, props_methods=props_methods, tmpdir=tmpdir, invariant_type=cfr_inv_type,
                                 only_john=only_john, nodes_to_refine=nodes_to_refine)
        sufix = "_cfr" + str(it + 1)
        OM.lazy_printif(1, lambda: summary("CFG({})".format(it + 1), pe_cfg))
        if config.get("show_with_invariants", False) and cfr_inv:
            sufix += "_with_inv_" + str(cfr_inv_type)
    OM.printseparator(1)
    showgraph(pe_cfg, config, sufix=sufix, invariant_type=cfr_inv_type, console=console, writef=writef)
    return pe_cfg


def partialevaluate(cfg, props_methods=[], tmpdir=None, invariant_type=None, only_john=False, nodes_to_refine=None):
    if tmpdir is None or tmpdir == "":
        import tempfile
        tmpdirname = tempfile.mkdtemp()
    else:
        tmpdirname = tmpdir
    import random
    tmpplfile = os.path.join(tmpdirname, "source_%06x.pl" % random.randrange(16**6))
    OM.printif(3, "system prolog file ", tmpplfile)
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
    initNode = "n_{}{}".format(saveName(init_node), vs)
    if OM.verbosity > 2:
        with open(tmpplfile, 'r') as fin:
            OM.printif(3, fin.read())

    # PROPERTIES
    propsfile = set_props(cfg, tmpdirname, props_methods=props_methods, pl_file=tmpplfile, entry=initNode,
                          nodes_to_refine=nodes_to_refine, invariant_type=invariant_type, only_john=only_john)

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
    pe_cfg.build_polyhedrons()
    rmded = pe_cfg.remove_unsat_edges()
    if len(rmded) > 0:
        OM.printif(1, "Removed edges {} because they where unsat.".format(rmded))
    OM.lazy_printif(4, lambda: fcpeprogram.decode("utf-8"))
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


def set_props(cfg, tmpdirname, props_methods, pl_file, entry, nodes_to_refine, invariant_type, only_john):
    gvars = cfg.get_info("global_vars")
    gvars = gvars[:int(len(gvars) / 2)]
    pvars = _plVars(len(gvars))
    propsfile = os.path.join(tmpdirname, "source_output/source.props")
    basedir = os.path.dirname(propsfile)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    open(propsfile, 'a').close()
    from nodeproperties.cfrprops import compute_cfrprops
    in_nodes_to_refine = nodes_to_refine
    if "cfr_john_properties" in props_methods:
        jh_p = johns_props1(cfg, pl_file, entry, propsfile, nodes_to_refine)
        if only_john:
            in_nodes_to_refine = [n for n in jh_p if len(jh_p[n]) > 0]
            OM.printif(1, "johns nodes: ", in_nodes_to_refine)
    props = compute_cfrprops(cfg, in_nodes_to_refine, modes=props_methods, invariant_type=invariant_type)

    _add_props(propsfile, props, gvars, pvars)

    # SAVE PROPS
    OM.printif(2, "CFR with props: {}".format(props))
    if "cfr_john_properties" in props_methods:
        OM.printif(2, "CFR john props: {}".format(jh_p))
    return propsfile


def _plVars(N):
    from string import ascii_uppercase
    ABC = list(ascii_uppercase)
    lenABC = len(ABC)
    plvars = ABC[:N]
    if N > lenABC:
        plvars += [ABC[i % lenABC] + str(int(i / lenABC)) for i in range(lenABC, N)]
    return plvars


def saveName(word):
    return re.sub('[\'\?\!\^.]', '_P', word)


def _add_props(filename, props, gvars, pvars):
    vars_str = ",".join(pvars)
    renamedvars = lambda v: pvars[gvars.index(v)]
    with open(filename, "a") as f:
        for node in props:
            for cons in props[node]:
                cons_str = ", ".join([c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                                      for c in cons])
                line = "n_{}({}) :- [{}].\n".format(saveName(node), vars_str, cons_str)
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
    # t_names = [e["name"] for e in scc_edges]
    all_names = [e["name"] for e in cfg.get_edges()]
    it = 0
    from copy import deepcopy
    entries = scc.get_info("entry_nodes")
    for entry in entries:
        num_t = 0
        for t in []:  # cfg.get_edges(target=entry):
            name = t["name"]
            old_src = t["source"]
            if old_src in nodes:
                continue
            num_t += 1
            src = t["source"]
            new_t = deepcopy(t)
            new_t["source"] = init_node
            name = "tr" + str(it)
            it += 1
            while name in all_names:
                name = "tr" + str(it)
                it += 1
            all_names += [name]
            new_t["name"] = name
            tr_poly = t["polyhedron"].copy()
            try:
                inv = cfg.nodes[src][inv_name].get_constraints()
            except Exception:
                inv = []
            tr_poly.add_constraints(inv)
            new_t["polyhedron"] = tr_poly
            scc_copy.add_edge(**new_t)
        if num_t == 0:
            name = "tr" + str(it)
            it += 1
            while name in all_names:
                name = "tr" + str(it)
                it += 1
            all_names += [name]
            new_t = {"source": init_node, "target": entry, "name": name}
            try:
                inv = cfg.nodes[entry][inv_name].get_constraints()
            except Exception:
                inv = []
            new_t["local_vars"] = []
            new_t["constraints"] = inv
            new_t["polyhedron"] = C_Polyhedron(inv, variables=cfg.get_info("global_vars"))
            scc_copy.add_edge(**new_t)
    scc_copy.set_info("init_node", init_node)
    scc_copy.set_info("entry_nodes", [init_node])
    return scc_copy


def johns_props1(cfg, tmpplfile, entry, propsfile, nodes_to_refine):
    gvars = cfg.get_info("global_vars")
    gvars = gvars[:int(len(gvars) / 2)]
    pvars = _plVars(len(gvars))
    propspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', 'props1.sh')
    pipe = Popen([propspath, tmpplfile, entry, '-r', propsfile],
                 stdout=PIPE, stderr=PIPE)
    ___, err = pipe.communicate()
    if err is not None and err:
            raise Exception(err)
    if nodes_to_refine is not None:
        nodes_to_remove = [n for n in cfg.get_nodes() if n not in nodes_to_refine]
        remove_nodes_props(propsfile, nodes_to_remove)
    au_props = _parse_props(propsfile, gvars, pvars)
    cfg.set_nodes_info(au_props, "cfr_auto_properties")
    return au_props


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
        if begincons + 1 == endcons:
            continue
        strs_cons = line[begincons + 1:endcons].split(",")
        from genericparser import parse_constraint
        cons = [parse_constraint(_translate(c, correspondance)) for c in strs_cons if c != ""]
        if len(cons) == 0:
            continue
        if node_name not in props:
            props[node_name] = []
        props[node_name].append(cons)
    return props


def remove_nodes_props(filename, nodes):
    from shutil import move
    destfile = filename + ".tmp"
    ops = tuple([("n_{}(".format(saveName(n))) for n in nodes])
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

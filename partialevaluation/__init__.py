import os
from subprocess import PIPE
from subprocess import Popen
    
__all__ = ['partialevaluate']


def partialevaluate(cfg, auto_props=4, user_props=None, fcpath=None, tmpdir=None, debug=False, invariant_type=None, only_nodes=None, add_props={} ):
    if not(auto_props in range(0, 5)):
        raise ValueError("CFR automatic propertis mode unknown: {}.".format(auto_props))
    
    if tmpdir is None:
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
    if debug:
        with open(tmpplfile, 'r') as fin:
            print(fin.read())


    # PROPERTIES
    propsfile, props = compute_props(tmpdirname, tmpplfile, auto_props, only_nodes, add_props, cfg.get_info("global_vars")[:N], debug=debug)
    cfg.set_nodes_info(props, "cfr_auto_properties")
    
    if user_props is not None:
        pass
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
    from termination.output import Output_Manager as OM
    OM.printf("simplifying after cfr.")
    pe_cfg.simplify_constraints()

    if fcpath:
        pe_cfg.toFc(fcpath)

    if debug:
        print(fcpeprogram.decode("utf-8"))
    return pe_cfg
    

def compute_props(tmpdirname, tmpplfile, level, only_nodes, add_props, gvars, debug=False):
    propspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin','props.sh')
    pipe = Popen([propspath, tmpplfile, '-l', str(level), '-r', tmpdirname],
                 stdout=PIPE, stderr=PIPE)
    propsfile, err = pipe.communicate()
    if err is not None and err:
            raise Exception(err)
    propsfile = propsfile.decode("utf-8")
    pvars = _plVars(len(gvars))
    props = _parse_props(propsfile, gvars, pvars)
    if debug:
        with open(propsfile, "r") as f:
            print(f.read())
    #props = _do_modifications(props)
    #_print_props(propsfile, props, gvars, pvars)
    return propsfile, props

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


def _print_props(filename, props, gvars, pvars):
    vars_str = ",".join(pvars)
    renamedvars = lambda v: pvars[gvars.index(v)]
    with open(filename, "w") as f:
        for node in props:
            for cons in props[node]:
                cons_str = ", ".join([c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                                      for c in cons])
                line = "n_{}({}) :- [{}].\n".format(node,vars_str, cons_str)
                f.write(line)

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

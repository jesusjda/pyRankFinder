import os
from termination.output import Output_Manager as OM
from subprocess import PIPE
from subprocess import Popen
    
__all__ = ['partialevaluate']


def partialevaluate(cfg, auto_props=4, user_props=False, tmpdir=None, invariant_type=None, nodes_to_refine=[]):
    if not(auto_props in range(0, 5)):
        raise ValueError("CFR automatic properties mode unknown: {}.".format(auto_props))
    
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
    if OM.verbosity > 2:
        with open(tmpplfile, 'r') as fin:
            OM.printif(3, fin.read())


    # PROPERTIES
    propsfile = set_props(cfg, tmpdirname, tmpplfile, auto_props, user_props, nodes_to_refine)

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
    

def set_props(cfg, tmpdirname, tmpplfile, auto_props, user_props, nodes_to_refine):
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

    if user_props:
        node_data = cfg.get_nodes(data=True)

        usr_props = {}
        for node, data in node_data:
            if "cfr_properties" in data:
                n_props = [p for p in data["cfr_properties"]]
                if len(n_props) > 0:
                    usr_props[node] = n_props
        _add_props(propsfile, usr_props, gvars, pvars)

    if len(nodes_to_refine) > 0:
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
    print(ops)
    with open(filename, "r") as fin, open(destfile, "w") as fout:
        for line in fin:
            if not line.startswith(ops):
                fout.write(line)
    move(destfile, filename)

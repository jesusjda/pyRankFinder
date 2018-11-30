def max_dim(edges):
    maximum = 0
    for e in edges:
        d = e["polyhedron"].get_dimension()
        d -= len(e["local_vars"])
        if d > maximum:
            maximum = d
    return maximum


def get_rf(variables, point):
    """
    Assume variables[0] is the independent term
    the result point has as coord(0) the indep term
    """
    from ppl import Linear_Expression
    from ppl import Variable
    from ppl import point as pplpoint
    exp = Linear_Expression(0)
    for i in range(len(variables)):
        exp += point.coefficient(variables[i])*Variable(i)
    return pplpoint(exp)


def get_use_z3(algorithm, use_z3=None):
    if use_z3 is None:
        if "lib" in algorithm:
            return algorithm["lib"] == "z3"
        return False
    else:
        return use_z3


def get_z3_transition_polyhedron(tr, global_vars):
    local_vars = tr["local_vars"]
    all_vars = global_vars + local_vars
    cons = tr["constraints"]
    constrs = [c.transform(all_vars, lib="z3")
               for c in cons]
    return constrs

def get_ppl_transition_polyhedron(tr, global_vars):
    local_vars = tr["local_vars"]
    all_vars = global_vars + local_vars
    cons = tr["constraints"]
    constrs = [c.transform(all_vars, lib="z3")
               for c in cons]
    return constrs

def generate_names(vs, others):
    names = []
    variables = vs + others
    for v in vs:
        pv = v
        while (pv != v and pv in variables) or pv in names:
            pv += "'"
        names.append(pv)
    return names

def generate_prime_names(vs, others):
    names = []
    variables = vs + others
    for v in vs:
        pv = v + "'"
        while pv in variables or pv in names:
            pv += "'"
        names.append(pv)
    return names

def merge(base, to_add):
    result = base
    for key in to_add:
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(to_add[key])
        else:
            result[key] = [to_add[key]]
    return result

def showgraph(cfg, config, sufix="", invariant_type="none", console=False, writef=False):
    import os
    from termination.output import Output_Manager as OM
    if not console and not writef:
        return
    name = config["name"] +str(sufix)
    destname = config["output_destination"]
    if destname is None:
        return
    show_with_inv = config["show_with_invariants"] if "show_with_invariants" in config else False
    os.makedirs(os.path.dirname(destname), exist_ok=True)
    if not show_with_inv:
        invariant_type = "none"
    print(invariant_type)
    from io import StringIO
    stream = StringIO()
    if "fc" in config["output_formats"]:
        cfg.toFc(stream, invariant_type=invariant_type)
        fcstr=stream.getvalue()
        if console:
            OM.printif(0, "Graph {}".format(name), consoleid="source", consoletitle="Fc Source")
            OM.printif(0, fcstr, format="text", consoleid="source", consoletitle="Fc Source")
        if writef:
            OM.writefile(0, name+".fc", fcstr)
        stream.close()
        stream = StringIO()
    if "dot" in config["output_formats"] or "svg" in config["output_formats"]:
        cfg.toDot(stream, invariant_type=invariant_type)
        dotstr = stream.getvalue()
        dotfile = os.path.join(destname, name+".dot")
        os.makedirs(os.path.dirname(dotfile), exist_ok=True)

        with open(dotfile, "w") as f:
            f.write(dotstr)
        stream.close()
        stream = StringIO()
        if "dot" in config["output_formats"] and writef:
            if console:
                OM.printif(0, "Graph {}".format(name), consoleid="graphs", consoletitle="Graphs")
                OM.printif(0, dotstr, format="text", consoleid="graphs", consoletitle="Graphs")
            if writef:
                OM.writefile(0, name+".dot", dotstr)
        if "svg" in config["output_formats"]:
            svgfile = os.path.join(destname, name+".svg")
            svgstr = dottoSvg(dotfile, svgfile)
            if console:
                OM.printif(0, "Graph {}".format(name), consoleid="graphs", consoletitle="Graphs")
                OM.printif(0, svgstr, format="svg", consoleid="graphs", consoletitle="Graphs")
            if writef:
                OM.writefile(0, name+".svg", svgstr)
    if "koat" in config["output_formats"]:
        cfg.toKoat(path=stream, goal_complexity=True, invariant_type=invariant_type)
        koatstr=stream.getvalue()
        OM.printif(0, "Graph {}".format(name), consoleid="koat", consoletitle="koat Source")
        OM.printif(0, koatstr, format="text", consoleid="koat", consoletitle="koat Source")
        OM.writefile(0, name+".koat", koatstr)
        stream.close()
        stream = StringIO()
    if "pl" in config["output_formats"]:
        cfg.toProlog(path=stream, invariant_type=invariant_type)
        koatstr=stream.getvalue()
        OM.printif(0, "Graph {}".format(name), consoleid="pl", consoletitle="pl Source")
        OM.printif(0, koatstr, format="text", consoleid="pl", consoletitle="pl Source")
        OM.writefile(0, name+".pl", koatstr)
        stream.close()
        stream = StringIO()
    stream.close()

def dottoSvg(dotfile, svgfile):
    from subprocess import check_call
    check_call(['dot', '-Tsvg', dotfile ,'-o', svgfile])
    check_call(['sed', '-i','-e', ':a', '-re', '/<!.*?>/d;/<\?.*?>/d;/<!/N;//ba', svgfile])
    svgstr = ""
    with open(svgfile, "r") as f:
        svgstr += f.read()
    return svgstr

def file2string(filepath):
    with open(filepath, 'r') as f:
        data=f.read()
    return data

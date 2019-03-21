def get_rf(coeff_variables, variables, point):
    """
    Assume variables[0] is the independent term
    the result point has as coord(0) the indep term
    """
    from lpi import Expression
    exp = Expression(point[0][coeff_variables[0].get_variables()[0]])
    for i in range(1, len(coeff_variables)):
        ci = point[0][coeff_variables[i].get_variables()[0]]
        exp += ci * Expression(variables[i - 1])
    return exp


def generate_names(vs, others, init_sufix=""):
    names = []
    variables = vs + others
    for v in vs:
        pv = v + init_sufix
        while (pv != v and pv in variables) or pv in names:
            pv += "'"
        names.append(pv)
    return names


def generate_prime_names(vs, others):
    return generate_names(vs, others, "'")


def get_free_name(others, name="x", num=1):
    names = []
    variables = others
    i = 0
    for __ in range(num):
        v = name + str(i)
        i += 1
        while v in variables or v in names:
            v = name + str(i)
            i += 1
        names.append(v)
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


def showgraph(cfg, config, sufix="", invariant_type="none", console=False, writef=False, output_formats=None):
    import os
    from termination.output import Output_Manager as OM
    if not console and not writef:
        return
    name = config["name"] + str(sufix)
    destname = config["output_destination"] if config["output_destination"] is not None else ""
    completename = os.path.join(destname, name)
    tmpdir = config["tmpdir"]
    show_with_inv = config.get("show_with_invariants", False)
    # os.makedirs(os.path.dirname(completename), exist_ok=True)
    if output_formats is None:
        output_formats = config["output_formats"]
    if not show_with_inv:
        invariant_type = "none"
    from io import StringIO
    stream = StringIO()
    if "fc" in output_formats:
        cfg.toFc(stream, invariant_type=invariant_type)
        fcstr = stream.getvalue()
        if console:
            OM.printif(0, "Graph {}".format(name), consoleid="source", consoletitle="Fc Source")
            OM.printif(0, fcstr, format="text", consoleid="source", consoletitle="Fc Source")
        if writef:
            OM.writefile(0, completename + ".fc", fcstr)
        stream.close()
        stream = StringIO()
    if "dot" in output_formats or "svg" in output_formats:
        cfg.toDot(stream, invariant_type=invariant_type)
        dotstr = stream.getvalue()
        dotfile = os.path.join(tmpdir, name + ".dot")
        os.makedirs(os.path.dirname(dotfile), exist_ok=True)

        with open(dotfile, "w") as f:
            f.write(dotstr)
        stream.close()
        stream = StringIO()
        if "dot" in output_formats and writef:
            if console:
                OM.printif(0, "Graph {}".format(name), consoleid="graphs", consoletitle="Graphs")
                OM.printif(0, dotstr, format="text", consoleid="graphs", consoletitle="Graphs")
            if writef:
                OM.writefile(0, completename + ".dot", dotstr)
        if "svg" in output_formats:
            svgfile = os.path.join(tmpdir, name + ".svg")
            svgstr = dottoSvg(dotfile, svgfile)
            if console:
                OM.printif(0, "Graph {}".format(name), consoleid="graphs", consoletitle="Graphs")
                OM.printif(0, svgstr, format="svg", consoleid="graphs", consoletitle="Graphs")
            if writef:
                OM.writefile(0, completename + ".svg", svgstr)
    if "koat" in output_formats:
        cfg.toKoat(path=stream, goal_complexity=True, invariant_type=invariant_type)
        koatstr = stream.getvalue()
        if console:
            OM.printif(0, "Graph {}".format(name), consoleid="koat", consoletitle="koat Source")
            OM.printif(0, koatstr, format="text", consoleid="koat", consoletitle="koat Source")
        if writef:
            OM.writefile(0, completename + ".koat", koatstr)
        stream.close()
        stream = StringIO()
    if "pl" in output_formats:
        cfg.toProlog(path=stream, invariant_type=invariant_type)
        koatstr = stream.getvalue()
        if console:
            OM.printif(0, "Graph {}".format(name), consoleid="pl", consoletitle="pl Source")
            OM.printif(0, koatstr, format="text", consoleid="pl", consoletitle="pl Source")
        if writef:
            OM.writefile(0, completename + ".pl", koatstr)
        stream.close()
        stream = StringIO()
    stream.close()


def dottoSvg(dotfile, svgfile):
    from subprocess import check_call
    from subprocess import CalledProcessError
    svgstr = ""
    try:
        check_call(['dot', '-Tsvg', dotfile, '-o', svgfile])
        check_call(['sed', '-i', '-e', ':a', '-re', '/<!.*?>/d;/<\?.*?>/d;/<!/N;//ba', svgfile])
        with open(svgfile, "r") as f:
            svgstr += f.read()
    except CalledProcessError:
        pass
    return svgstr


def file2string(filepath):
    with open(filepath, 'r') as f:
        data = f.read()
    return data


def compute_way_nodes(cfg, target_nodes):
    way_nodes = set()
    init = cfg.get_info("init_node")
    for n in target_nodes:
        ns = cfg.get_all_nodes_between(init, n)
        way_nodes.update(ns)
    return way_nodes

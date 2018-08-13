
def partialevaluate(cfg, level=4, fcpath=None, tmpdir=None, debug=False):
    if level == 0:
        return cfg
    if not(level in range(1, 5)):
        raise ValueError("PE level unknown: {}.".format(level))
    import os
    from subprocess import PIPE
    from subprocess import Popen
    from genericparser.Parser_fc import Parser_fc
    pepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin','pe.sh')
    
    if tmpdir is None:
        import tempfile
        tmpdirname = tempfile.mkdtemp()
    else:
        tmpdirname = tmpdir
    tmpplfile = os.path.join(tmpdirname, "source.pl")
    cfg.toProlog(path=tmpplfile)
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
    pipe = Popen([pepath, tmpplfile, initNode, '-p', '-l', str(level), '-r', tmpdirname],
                 stdout=PIPE, stderr=PIPE)
    fcpeprogram, err = pipe.communicate()
    if err is not None and err:
            raise Exception(err)
    pfc = Parser_fc()
    if fcpath:
        with open(fcpath, "w") as text_file:
            text_file.write(fcpeprogram.decode("utf-8"))
    if debug:
        print(fcpeprogram.decode("utf-8"))
    return pfc.parse_string(fcpeprogram.decode("utf-8"))
    

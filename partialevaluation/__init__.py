def partialevaluate(cfg, level="full"):
    if level not in ["full", "simple"]:
        raise ValueError("PE level unknown: {}.".format(level))
    import os
    import tempfile
    from subprocess import PIPE
    from subprocess import Popen
    pepath = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), 'bin','pe.sh')
    
    tmpdirname = tempfile.mkdtemp()
    tmppropsfile = os.path.join(tmpdirname, "props.props")
    tmpplfile = os.path.join(tmpdirname, "source.pl")       
    cfg.toProlog(path=tmpplfile)
    pipe = Popen([pepath, tmpplfile, level, tmppropsfile],
                 stdout=PIPE, stderr=PIPE)
    out, err = pipe.communicate()
    print("#"*40)
    print("out: "+str(out))
    print("#"*40)
    print("#"*40)
    print("err: "+str(err))
    print("#"*40)
    
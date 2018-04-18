from termination.profiler import register_as
@register_as("pe")
def partialevaluate(cfg, level="full", fcpath=None):
    if level == "none":
        return cfg
    if level == "complete":
        level = "full"
    if not(level in ["full", "simple"]):
        raise ValueError("PE level unknown: {}.".format(level))
    import os
    import tempfile
    from subprocess import PIPE
    from subprocess import Popen
    from genericparser.Parser_fc import Parser_fc
    pepath = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), 'bin','pe.sh')
    
    tmpdirname = tempfile.mkdtemp()
    tmppropsfile = os.path.join(tmpdirname, "props.props")
    tmpplfile = os.path.join(tmpdirname, "source.pl")
    cfg.toProlog(path=tmpplfile)
    #with open(tmpplfile, 'r') as fin:
    #    print(fin.read())
    pipe = Popen([pepath, tmpplfile, level, tmppropsfile],
                 stdout=PIPE, stderr=PIPE)
    fcpeprogram, err = pipe.communicate()
    if err is not None and err:
            raise Exception(err)
    pfc = Parser_fc()
    if fcpath:
        with open(fcpath, "w") as text_file:
            text_file.write(fcpeprogram.decode("utf-8"))
    return pfc.parse_string(fcpeprogram.decode("utf-8"))
    

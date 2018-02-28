import argparse
from multiprocessing import Manager
from multiprocessing import Process
import os
import sys
import termination

import rankfinder


def setArgumentParser():
    desc = "Generator"
    argParser = argparse.ArgumentParser(description=desc)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    argParser.add_argument("--dotDestination", required=False,
                           help="Folder to save dot graphs.")
    # Algorithm Parameters
    argParser.add_argument("-mo", "--memoryout", type=int, default=None,
                           help="")
    argParser.add_argument("-to", "--timeout", type=int, default=None,
                           help="")
    argParser.add_argument("-sccd", "--scc_depth", type=int,
                           choices=range(0, 10), default=5,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-sc", "--simplify_constraints", required=False,
                           action='store_true', help="Simplify constraints")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-c", "--cache", required=True,
                           help="Folder cache.")
    return argParser


def vm(func, args=(), kwargs={}, time_segs=60, memory_mb=None, out=None, default=None):
    manager = Manager()
    return_dict = manager.dict()

    def worker(work, memory_mb, returndata):
        import resource
        if memory_mb:
            memory_mb *= 1024*1024
            _, hard = resource.getrlimit(resource.RLIMIT_DATA)
            resource.setrlimit(resource.RLIMIT_DATA, (memory_mb, hard))
        returndata[0] = work(*args)
        return 0

    p = Process(target=worker, args=(func, memory_mb, return_dict,), kwargs=kwargs)
    p.start()
    p.join(time_segs)
    if p.is_alive():
        p.terminate()
        print("TIMEOUT")
        if out is not None:
            tmpfile = os.path.join(os.path.curdir, out)
            with open(tmpfile, "w") as f:
                f.write("TIMEOUT\n")
        return default
    if not return_dict:
        print("TIMEOUT")
        print("MEMORYOUT")
        if out is not None:
            tmpfile = os.path.join(os.path.curdir, out)
            with open(tmpfile, "w") as f:
                f.write("TIMEOUT\n")
                f.write("MEMORYOUT\n")
        return default
    return return_dict[0]


if __name__ == "__main__":
    argParser = setArgumentParser()
    args = argParser.parse_args(sys.argv[1:])
    ar = vars(args)
    cachedir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), ar["cache"])
    files = ar["files"]
    sccd = ar["scc_depth"]
    dotF = ar["dotDestination"]
    verb = ar["verbosity"]
    lib = ["ppl"]
    inv = ["none", "basic"]
    dt = ["iffail"]
    if "timeout" in ar and ar["timeout"]:
        tout = int(ar["timeout"])
    else:
        tout = None
    if "memoryout" in ar and ar["memoryout"]:
        mout = int(ar["memoryout"])
    else:
        mout = None
    algs = []
    algs.append([termination.algorithm.lrf.PR()])
    for i in range(1, 3):
        algs.append([termination.algorithm.qnlrf.QNLRF({"max_depth": i, "min_depth": i,
                                                        "version": 1})])
    #algs.append([{"name": "qlrf_bg"}])

    status = {}
    for l in lib:
        for a in algs:
            a[0].set_prop("lib",l)
            for i in inv:
                for d in dt:
                    for f in files:
                        print("Launching: "+f)
                        name = os.path.basename(f)
                        tag = a[0].NAME
                        if a[0].has_prop("max_depth"):
                            tag += "_" + str(a[0].get_prop("max_depth"))
                        tag += "_" + d[0] + "_" + i[0]
                        o = name + "." + tag + "_" + l + ".cache"
                        o = os.path.join(cachedir, o)
                        if not(f in status):
                            status[f] = False
                        if status[f]:
                            if os.path.isfile(o):
                                os.remove(o)
                            continue
                        if l == "z3":
                            tmpfile = name + "." + tag + "_ppl.cache"
                            tmpfile = os.path.join(cachedir, tmpfile)
                            if os.path.isfile(tmpfile):
                                if not('TIMEOUT' in open(tmpfile).read()):
                                    print("Skip")
                                    if os.path.isfile(o):
                                        os.remove(o)
                                    continue
                            else:
                                if os.path.isfile(o):
                                        os.remove(o)
                                continue
                        tag += "_" + l
                        if os.path.isfile(o):
                            os.remove(o)
                        print("Trying with : " + tag)
                        config = {
                            "scc_depth": sccd,
                            "dotDestination": dotF,
                            "verbosity": verb,
                            "ei_out": False,
                            "algorithms": a,
                            "invariants": i,
                            "different_template": d,
                            "simplify_constraints": True,
                            "files": [f],
                            "output": [o]
                        }
                        if tout is None:
                            found = rankfinder.launch_file(config, f, o)
                        else:
                            found = vm(rankfinder.launch_file, time_segs=tout,
                                       args=(config, f, o), out=o,
                                       memory_mb=mout, default=False)
                        status[f] = found

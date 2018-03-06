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


def sandbox(task, args=(), kwargs={}, time_segs=60, memory_mb=None, out=None, default=None):
    def worker(task, r_dict, *args, **kwargs):
        try:
            r_dict[0] = task(*args, **kwargs)
            r_dict["status"] = "ok"
        except MemoryError as e:
            r_dict["status"] = "MemoryLimit"
        except Exception as e:
            r_dict["status"] = "ERROR " + type(e).__name__
            raise Exception() from e
    def returnHandler(exitcode, r_dict, usage=None, out=None, default=None):
        msg = ""
        ret = default
        try:
            if exitcode == -24:
                msg += "TIMEOUT"
            elif exitcode <0:
                msg += "ERROR"
            elif r_dict["status"] == "ok":
                msg += str(r_dict[0])
                ret = r_dict[0]
            else:
                msg += r_dict["status"]
        except Exception as e:
            msg += "ERROR while processing output "
            msg += type(e).__name__
        finally:
            if usage:
                msg += "\n\nTime: {}s\n Mem: {}B".format(usage[0]+usage[1], usage[2])
            print(msg)
            if out is not None:
                tmpfile = os.path.join(os.path.curdir, out)
                with open(tmpfile, "w") as f:
                    f.write(msg)
            return ret
                
    manager = Manager()
    r_dict = manager.dict()   
    import resource
    if memory_mb:
        bML = 1024*1024*memory_mb
    else:
        bML = resource.RLIM_INFINITY
    if time_segs:
        sTL = time_segs
    else:
        sTL = resource.RLIM_INFINITY
    softM, hardM = resource.getrlimit(resource.RLIMIT_DATA)
    softT, hardT = resource.getrlimit(resource.RLIMIT_CPU)
    p=Process(target=worker, args=(task, r_dict, *args), kwargs=kwargs)
    try: 
        from resource import prlimit
        p.start()
        prlimit(p.pid, resource.RLIMIT_CPU, (sTL, hardT))
        prlimit(p.pid, resource.RLIMIT_DATA, (bML, hardM))
    except ImportError:
        resource.setrlimit(resource.RLIMIT_CPU, (sTL, hardT))
        resource.setrlimit(resource.RLIMIT_DATA, (bML, hardM))
        p.start()
    finally:
        p.join()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        resource.setrlimit(resource.RLIMIT_CPU, (softT, hardT))
        resource.setrlimit(resource.RLIMIT_DATA, (softM, hardM))
        return returnHandler(p.exitcode, r_dict, usage, out=out, default=default)  

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
                                if not('TIMEOUT' in open(tmpfile).read() or
                                       'MemoryLimit' in open(tmpfile).read() or
                                       'ERROR' in open(tmpfile).read()):
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
                            "termination": a,
                            "invariants": i,
                            "different_template": d,
                            "simplify_constraints": True,
                            "files": [f],
                            "output": [o]
                        }

                        status[f] = sandbox(rankfinder.launch_file, args=(config, f, o),
                                            time_segs=tout, memory_mb=mout,
                                            out=o, default=False)

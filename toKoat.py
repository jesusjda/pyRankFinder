import argparse
from partialevaluation import partialevaluate
from multiprocessing import Manager
from multiprocessing import Process


def setArgumentParser():
    desc = "Generator"
    argParser = argparse.ArgumentParser(description=desc)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    # Algorithm Parameters
    argParser.add_argument("-mo", "--memoryout", type=int, default=None,
                           help="")
    argParser.add_argument("-to", "--timeout", type=int, default=None,
                           help="")
    argParser.add_argument("-pe", "--partial_evaluate", type=int, required=False, nargs='+',
                           default=[0], choices=range(0, 5), help="Partial Evaluate")
    argParser.add_argument("-i", "--invariants", nargs='+', required=False, choices=["none", "basic"],
                           default=["none"], help="Compute Invariants.")
    argParser.add_argument("-pt", "--pe_times", type=int, choices=range(0, 5),
                           help="# times to apply pe", default=1)
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-c", "--cache", required=True,
                           help="Folder cache.")
    return argParser


def sandbox(task, args=(), kwargs={}, time_segs=60, memory_mb=None, out=None, default=None):
    manager = Manager()
    r_dict = manager.dict()
    def worker(task, r_dict, *args, **kwargs):
        try:
            r_dict[0] = task(*args, **kwargs)
            r_dict["status"] = "ok"
        except MemoryError as e:
            r_dict["status"] = "MemoryLimit"
        except Exception as e:
            r_dict["status"] = "ERROR " + type(e).__name__
            raise

    def returnHandler(exitcode, r_dict, usage=None, out=None, default=None):
        msg = ""
        ret = default
        try:
            if exitcode == -24:
                msg += "TIMEOUT"
            elif exitcode < 0:
                msg += "ERROR"
            elif not("status" in r_dict):
                msg += "TIMEOUT" 
            elif r_dict["status"] == "ok":
                msg += str(r_dict[1])
                ret = r_dict[0]
            else:
                msg += r_dict["status"]
        except Exception as e:
            msg += "ERROR while processing output "
            msg += type(e).__name__
        finally:
            if usage:
                msg += "\n\nTime: {}s\n Mem: {}B\n".format(usage[0] + usage[1], usage[2])
            print(msg)
            if out is not None:
                tmpfile = os.path.join(os.path.curdir, out)
                with open(tmpfile, "w") as f:
                    f.write(msg)
            return ret
    import resource
    if memory_mb:
        bML = 1024 * 1024 * memory_mb
    else:
        bML = resource.RLIM_INFINITY
    if time_segs:
        sTL = time_segs
    else:
        sTL = resource.RLIM_INFINITY
    softM, hardM = resource.getrlimit(resource.RLIMIT_DATA)
    softT, hardT = resource.getrlimit(resource.RLIMIT_CPU)
    p = Process(target=worker, args=(task, r_dict, *args), kwargs=kwargs)
    # worker(task, r_dict, *args,**kwargs)
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
        # return returnHandler(p.exitcode, r_dict, usage, out=out, default=default)


def doit(f, g, pe, pe_times, inv, cachedir):
    from genericparser import GenericParser
    from rankfinder import compute_invariants
    from rankfinder import build_ppl_polyhedrons
    name = f.replace("/", "_")
    o = name
    if inv == "basic":
        o += "-INV"
    o += ".koat"
    o = os.path.join(cachedir, o)
    cfg = GenericParser().parse(f)

    build_ppl_polyhedrons(cfg)
    compute_invariants(inv, cfg)
    cfg.toKoat(path=o, goal_complexity=g, invariants=True)
    cfg.toDot(o + ".dot", minimize=False, invariants=False)
    # cfg.toSummary(o+"summary.json")
    for num in range(1, pe_times):
        o = name
        if pe == 4 and num > 0:
            o += "-PE"
            if num > 1:
                o += str(pe_times)
        if inv == "basic":
            o += "-INV"
        o += ".koat"
        o = os.path.join(cachedir, o)
        cfg = partialevaluate(cfg, level=pe, debug=False)

        build_ppl_polyhedrons(cfg)
        compute_invariants(inv, cfg)
        cfg.toKoat(path=o, goal_complexity=g, invariants=True)
        cfg.toDot(o + ".dot", minimize=False, invariants=False)
        # cfg.toSummary(o+"summary.json")


def toKoat(ar, cachedir):
    files = ar["files"]
    verb = ar["verbosity"]
    pe_modes = ar["partial_evaluate"]
    invariants = ar["invariants"]
    pe_times = ar["pe_times"]
    num = len(files)
    i = 1
    for f in files:
        if not os.path.isfile(f):
            print("File not found")
            continue
        if verb > 0:
            print("({}/{}) {}".format(i, num, f))
        i = i + 1
        goal_complexity = True
        for pe in pe_modes:
            if verb > 0:
                print("  >  > pe = " + str(pe))
            for inv in invariants:
                try:

                    sandbox(doit, args=(f, goal_complexity, pe, pe_times, inv, cachedir), time_segs=180)
                    
                except Exception as e:
                    print(e)
                    # raise Exception() from e


if __name__ == '__main__':
    import os
    import sys
    argParser = setArgumentParser()
    args = argParser.parse_args(sys.argv[1:])
    ar = vars(args)
    cachedir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), ar["cache"])
    toKoat(ar, cachedir)

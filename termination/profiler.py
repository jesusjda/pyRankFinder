def register_as(name):
    def decorator(func):
        from functools import wraps
        @wraps(func)
        def wrapper(*args,**kwargs):
            from time import time
            itime = time()
            OP.start(name,itime)
            try:
                result = func(*args,**kwargs)
                return result
            finally:
                ftime = time()
                OP.stop(ftime-itime)
        return wrapper
    return decorator
import sys
class OwnProfiler(object):
    
    def __init__(self, **kwargs):
        self.props = kwargs
        self.mesures = {}
        self.currentmethod = None
        self.currenttime = None

    def start(self, name, time):
        if name not in self.mesures:
            self.mesures[name] = {}
        if str(time) in self.mesures[name]:
            raise AssertionError("too many start calls")
        self.mesures[name][str(time)] = {"callermethod": self.currentmethod,
                                         "callertime":self.currenttime,
                                         "inittime": time,
                                         "childs":[]}
        if self.currentmethod is not None:
            self.mesures[self.currentmethod][self.currenttime]["childs"].append((name, str(time)))
        self.currentmethod = name
        self.currenttime = str(time)

    def stop(self, total):
        callermethod = self.mesures[self.currentmethod][self.currenttime]["callermethod"]
        callertime = self.mesures[self.currentmethod][self.currenttime]["callertime"]
        self.mesures[self.currentmethod][self.currenttime]["totaltime"] = total
        self.currentmethod = callermethod
        self.currenttime = callertime
    
    def toString(self, parent=None, time=None, totaltime=1, inittime=0, depth=0, maxdepth=10, output=""):
        if parent is None:
            for p in self.mesures:
                for t in self.mesures[p]:
                    if self.mesures[p][t]["callermethod"] is None:
                        output = self._print_unique(p, t, totaltime, inittime, depth, maxdepth, output)
        elif time is None:
            for t in self.mesures[parent]:
                output = self._print_unique(parent, t, totaltime, inittime, depth, maxdepth, output)
        else:
            output = self._print_unique(parent, time, totaltime, inittime, depth, maxdepth, output)
        return output
            
    def _print_unique(self, parent, time, totaltime, inittime, depth, maxdepth, output):
        tparent=self.mesures[parent][time]["totaltime"]
        ttime = self.mesures[parent][time]["inittime"]
        if depth == 0:
            totaltime = tparent
            inittime=ttime
        txt = "{}({},\t{:.5f})\t{:.5f}segs\t{:.2f}%\n".format("\t"*depth,parent,ttime-inittime,tparent,(tparent*100)/totaltime)
        output += txt
        if depth < maxdepth:
            for c in self.mesures[parent][time]["childs"]:
                output = self.toString(parent=c[0],time=c[1],totaltime=totaltime,inittime=inittime,depth=depth+1,maxdepth=maxdepth, output=output)
        elif len(self.mesures[parent][time]["childs"]) > 0:
            output += ("{}...\n".format("\t"*(depth+1)))
        return output

                
OP = OwnProfiler()
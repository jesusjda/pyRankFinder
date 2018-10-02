from __future__ import print_function

import eiol
import os
from ppl import Constraint
from ppl import Constraint_System
from ppl import Generator
from ppl import Linear_Expression
from ppl import Variable
import time
import xml.etree.ElementTree as ET


class Output:

    ei = False
    verbosity = 0
    _ei_commands = None
    _ei_actions = None
    destination = None
    outtxt = ""

    def __init__(self):
        self.inittime = time.time()
        try:
            self.initproctime = time.process_time()
        except AttributeError:
            self.initproctime = time.clock()
        self.prevtime = self.inittime
        self.prevproctime = self.initproctime
        self.ei = False
        self.verbosity = 0
        self.destination = None
        self.restart()

    def restart(self, ei=None, odest=None, cdest=None, vars_name=[], verbosity=None):
        if ei is not None:
            self.ei = ei
        self.destination = odest
        if self.ei:
            if cdest is None:
                self._ei_commands = eiol.eicommands()
                self._ei_actions = eiol.eiactions()
            else:
                self._ei_commands = eiol.eicommands(dest=cdest)
                self._ei_actions = eiol.eiactions(dest=cdest)
            self.cdest = cdest
        self._vars_name = vars_name
        self.outtxt = ""
        if verbosity is not None:
            self.verbosity = verbosity

    def printf(self, *kwargs):
        self.printif(0, *kwargs)

    def printseparator(self, verbosity=0):
        self.printif(verbosity, "#"*80)

    def printif(self, verbosity, *kwargs, format="text"):
        if self.verbosity < verbosity:
            return
        msg = ""
        acttime = time.time()
        try:
            actproctime = time.process_time()
        except AttributeError:
            actproctime = time.clock()
        if verbosity > 4:
            msg += "time -> program:{0:0>8}|step:{1:0>8}\n".format(acttime - self.inittime, acttime - self.prevtime)
            msg += "proc -> program:{0:0>8}|step:{1:0>8}\n".format(actproctime - self.initproctime, actproctime - self.prevproctime)
        self.prevtime = acttime
        self.prevproctime = actproctime
        first = True
        for m in kwargs:
            if not first:
                msg += " "
            first = False
            msg += self.tostr(m)
        if self.ei:
            if format == "html":
                txt = "<div>"+msg+"</div>"
            else:
                txt = msg
            c = eiol.content(format=format, text=txt)
            self._ei_commands.append(eiol.command_print(content=c, consoleid=self.cdest, consoletitle=self.cdest))
        elif self.destination is not None:
            self.outtxt += msg + '\n'
        else:
            print(msg)

    def print_rf_tr(self, verbosity, cfg, tr_name, rfs):
        if self.verbosity < verbosity:
            return
        return
        msg = "HI"  # rfs_tostring(rfs)
        if self.ei:
            c = eiol.content(format="text", text=msg)
            numl = str(cfg.get_edge(tr_name)["line"])
            d = {"from": numl}
            line = eiol.line(**d)
            ls = eiol.lines(line=line)
            self._ei_commands.append(
                eiol.command_addinlinemarker(lines=ls,
                                             content=c))
        else:
            print(tr_name + ":\n\t" + msg)

    def writefile(self, verbosity, path, content):
        if self.verbosity < verbosity:
            return
        if self.ei:
            c = eiol.command_writefile(overwrite="true",
                                       text=content,
                                       filename=str(path))
            self._ei_commands.append(c)
        else:
            tmpfile = os.path.join(os.path.curdir, path)
            with open(tmpfile, "w") as f:
                f.write(c)

    def show_output(self):
        if self.ei:
            # root = eiol.create_output(eicommands=self._ei_commands)
            out = ET.tostring(self._ei_commands,
                              encoding='utf8', method='xml')
            import re
            out = out.decode("utf-8")
            out = re.sub(r'<\?.*\?>', '', out)
        else:
            out = self.outtxt
        if self.destination is not None:
            tmpfile = os.path.join(os.path.curdir, self.destination)
            with open(tmpfile, "w") as f:
                f.write(out)
        else:
            print(out)
        return

    def tostr(self, cs, vars_name=None):
        response = ""
        if isinstance(cs, Constraint_System):
            constraints = [c for c in cs]
            response += "{"
            first = True
            for c in constraints:
                if not first:
                    response += ","
                first = False
                response += "\n  " + self.tostr(c, vars_name)
            if not first:
                response += "\n"
            response += "}"
            return response
        elif isinstance(cs, (Constraint, Linear_Expression, Generator)):
            ispoint = isinstance(cs, Generator)
            p = 0
            if ispoint:
                p = 1
            dim = cs.space_dimension()
            if vars_name is None:
                vars_name = self._vars_name
                for i in range(len(vars_name), dim):
                    vars_name.append("x" + str(i + p))
            first = True
            divisor = 1
            if ispoint:
                divisor = cs.divisor()
            for v in range(dim - p):
                coeff = cs.coefficient(Variable(v + p))
                if not first:
                    if coeff > 0:
                        response += " + "
                if coeff != 0:
                    first = False
                    if coeff < 0:
                        response += " - "
                        coeff = -coeff
                    if coeff != divisor and (coeff != 1 or divisor != 1): 
                        response += str(coeff)
                        if divisor != 1:
                            response += "/" + str(divisor)
                        response += " * "
                    response += vars_name[v]
            if ispoint:
                coeff = cs.coefficient(Variable(0))
            else:
                coeff = cs.inhomogeneous_term()
            if first or coeff != 0:
                if not first:
                    if coeff >= 0:
                        response += " + "
                if coeff < 0:
                    response += " - "
                    coeff = -coeff
                response += str(coeff)
                if divisor != 1:
                    response += "/" + str(divisor)
            if isinstance(cs, Constraint):
                if cs.is_inequality():
                    response += " >= "
                else:
                    response += " == "
                response += "0"
        else:
            response = str(cs)
        return response


Output_Manager = Output()

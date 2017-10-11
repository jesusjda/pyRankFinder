import xml.etree.ElementTree as ET
import eiol


class Output:

    ei = False
    verbosity = 0
    _ei_commands = None
    _ei_actions = None

    def __init__(self):
        self.ei = False
        self.verbosity = 0
        self._ei_commands = eiol.eicommands()
        self._ei_actions = eiol.eiactions()

    def printf(self, *kwargs):
        self.printif(0, kwargs)

    def printif(self, verbosity, *kwargs):
        msg = ""
        for m in kwargs:
            msg += m
        if self.verbosity >= verbosity:
            if self.ei:
                c = eiol.content(format="text", text=msg)
                self._ei_commands.append(eiol.command_print(content=c))
            else:
                print(kwargs)
        else:
            print("NO V", kwargs)

    def show_output(self):
        if self.ei:
            root = eiol.create_output(eicommands=self._ei_commands)
            print(ET.tostring(root, encoding='utf8', method='xml'))
        return

Output_Manager = Output()

from migen.fhdl.module import DUID
from migen.util.misc import xdir

from litex.soc.interconnect.csr_eventmanager import EventManager
from litex.soc.integration.doc import ModuleDoc

import textwrap
import inspect


def gather_submodules(module, depth=0, seen_modules=set(), submodules={
        "event_managers": [],
        "module_doc": [],
    }):
    if depth == 0:
        if isinstance(module, ModuleDoc):
            # print("{} is an instance of ModuleDoc".format(module))
            submodules["module_doc"].append(module)
    for k,v in module._submodules:
        # print("{}Submodule {} {}".format(" "*(depth*4), k, "xx"))
        if v not in seen_modules:
            seen_modules.add(v)
            if isinstance(v, EventManager):
                # print("{} appears to be an EventManager".format(k))
                submodules["event_managers"].append(v)

            if isinstance(v, ModuleDoc):
                submodules["module_doc"].append(v)

            gather_submodules(v, depth + 1, seen_modules, submodules)
    return submodules

class ModuleNotDocumented(Exception):
    """Indicates a Module has no documentation or sub-documentation"""
    pass

class DocumentedModule:
    """Multi-section Documentation of a Module"""

    def __init__(self, name, module):
        self.name = name
        self.sections = []
        has_documentation = False

        if isinstance(module, ModuleDoc):
            has_documentation = True
            self.sections.append(module)

        if hasattr(module, "get_module_documentation"):
            for doc in module.get_module_documentation():
                has_documentation = True
                self.sections.append(doc)

        if not has_documentation:
            raise ModuleNotDocumented()

    def print_region(self, stream, base_dir, note_pulses=False):
        title = "{}".format(self.name.upper())
        print(title, file=stream)
        print("=" * len(title), file=stream)
        print("", file=stream)

        for section in self.sections:
            print("{}".format(section.title()), file=stream)
            print("-" * len(section.title()), file=stream)
            print(section.body(), file=stream)
            print("", file=stream)


from migen.fhdl.module import DUID
from migen.util.misc import xdir

from litex.soc.interconnect.csr_eventmanager import EventManager

import textwrap

class ModuleDocumentation(DUID):

    def __init__(self, description=None, title=None, file=None):
        DUID.__init__(self)
        self._title = title
        self._lines = None
        self._finalized = False

        if file == None and description == None and self.__doc__ is None:
            raise ValueError("Must specify `file` or `description` when constructing a ModuleDescription()")
        if file is not None:
            with open(file, "r") as f:
                self.__doc__ = f.readAll()
        elif description is not None:
            self.__doc__ = description

    def finalize(self):
        if self._finalized:
            return
        self._finalized = True

        # Make the title out of the first line of documentation, if
        # it hasn't been specified yet.
        if self._title is None:
            self._lines = self.__doc__.splitlines()
            self._title = self._lines.pop(0)
            self.__doc__ = "\n".join(self._lines)

        self.__doc__ = textwrap.dedent(self.__doc__).strip()


    def title(self):
        self.finalize()
        return self._title

    def body(self):
        self.finalize()
        return self.__doc__


def gather_submodules(module, depth=0, seen_modules=set(), submodules={
        "event_managers": [],
        "module_doc": [],
    }):
    for k,v in module._submodules:
        # print("{}Submodule {} {}".format(" "*(depth*4), k, "xx"))
        if v not in seen_modules:
            seen_modules.add(v)
            if isinstance(v, EventManager):
                # print("{} appears to be an EventManager".format(k))
                submodules["event_managers"].append(v)

            if isinstance(v, ModuleDocumentation):
                submodules["module_doc"].append(v)

            gather_submodules(v, depth + 1, seen_modules, submodules)
    return submodules


def documentationprefix(prefix, documents, done):
    for doc in documents:
        if doc.duid not in done:
            # doc.name = prefix + doc.name
            done.add(csr.duid)

def _make_gatherer(method, cls, prefix_cb):
    def gatherer(self):
        try:
            exclude = self.autodoc_exclude
        except AttributeError:
            exclude = {}
        try:
            prefixed = self.__prefixed
        except AttributeError:
            prefixed = self.__prefixed = set()
        r = []
        for k, v in xdir(self, True):
            if k not in exclude:
                if isinstance(v, cls):
                    r.append(v)
                elif hasattr(v, method) and callable(getattr(v, method)):
                    items = getattr(v, method)()
                    prefix_cb(k + "_", items, prefixed)
                    r += items
        return sorted(r, key=lambda x: x.duid)
    return gatherer

class AutoDocument:
    """MixIn to provide documentation support.

    A module can inherit from the ``AutoDocument`` class, which provides ``get_module_documentation``.
    This will iterate through all objects looking for ones that inherit from ModuleDocumentation.

    If the module has child objects that implement ``get_csrs``, ``get_memories`` or ``get_constants``,
    they will be called by the``AutoCSR`` methods and their CSR and memories added to the lists returned,
    with the child objects' names as prefixes.
    """
    get_module_documentation = _make_gatherer("get_module_documentation", ModuleDocumentation, documentationprefix)

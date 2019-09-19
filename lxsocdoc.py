#!/usr/bin/env python3

# Disable pylint's E1101, which breaks completely on migen
#pylint:disable=E1101

from migen import *
from litex_boards.partner.targets.fomu import BaseSoC
from litex.soc.integration import SoCCore
from litex.soc.integration.soc_core import csr_map_update
from litex.soc.integration.builder import Builder
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import _CompoundCSR, CSRStatus, CSRStorage

class DocumentedCSR:
    def trim(docstring):
        if docstring is not None:
            import textwrap
            return textwrap.dedent(docstring).replace("\n", " ")
        
    def __init__(self, name, address, short_name="", reset=0, offset=0, size=8, description=None, fields=[]):
        self.name = name
        self.short_name = short_name
        self.address = address
        self.offset = offset
        self.size = size
        self.description = DocumentedCSR.trim(description)
        self.reset = reset
        self.fields = fields
        for f in self.fields:
            f.description = DocumentedCSR.trim(f.description)

class DocumentedCSRRegion:
    def __init__(self, csr_region):
        (self.name, self.origin, self.busword, self.raw_csrs) = csr_region
        self.current_address = self.origin
        self.csrs = []

        for csr in self.raw_csrs:
            self.document_csr(csr)

    def sub_csr_bit_range(self, csr, offset):
        nwords = (csr.size + self.busword - 1)//self.busword
        i = nwords - offset - 1
        nbits = min(csr.size - i*self.busword, self.busword) - 1
        name = (csr.name + str(i) if nwords > 1 else csr.name).upper()
        origin = i*self.busword
        return (origin, nbits, name)

    def split_fields(self, fields, start, end):
        """Split `fields` into a sub-list that only contains the fields
        between `start` and `end`.
        """
        return fields

    def print_reg(self, reg, stream):
        print("", file=stream)
        print("    .. wavedrom::", file=stream)
        print("        :caption: {}".format(reg.name), file=stream)
        print("", file=stream)
        print("        {", file=stream)
        print("            \"reg\": [", file=stream)
        if len(reg.fields) > 0:
            bit_offset = 0
            for field in reg.fields:
                term=","
                if bit_offset + field.size == self.busword:
                    term=""
                print("                {\"name\": \"" + field.name + "\",  \"bits\": " + str(field.size) + "}" + term, file=stream)
            bit_offset += field.size
            if bit_offset != self.busword:
                print("                {\"bits\": " + str(self.busword - bit_offset) + "}", file=stream)
        else:
            print("                {\"name\": \"" + reg.short_name + "[" + str(reg.offset + reg.size - 1) + ":" + str(reg.offset) + "]\",  \"bits\": " + str(reg.size) + "}", file=stream)
        print("            ], \"config\": {\"hspace\": 400, \"bits\": " + str(self.busword) + ", \"lanes\": 1 }, \"options\": {\"hspace\": 400, \"bits\": " + str(self.busword) + ", \"lanes\": 1}", file=stream)
        print("        }", file=stream)
        print("", file=stream)

    def document_csr(self, csr):
        """Generates one or more DocumentedCSR, which will get appended
        to self.csrs"""
        fields = []
        description = None
        atomic_write = False
        full_name = self.name.upper() + "_" + csr.name.upper()
        reset = 0

        if hasattr(csr, "fields"):
            fields = csr.fields.fields
        if hasattr(csr, "description"):
            description = csr.description
        if hasattr(csr, "atomic_write"):
            atomic_write = csr.atomic_write
        if hasattr(csr, "reset"):
            reset = csr.reset

        # If the CSR is composed of multiple sub-CSRs, document each
        # one individually.
        if isinstance(csr, _CompoundCSR) and len(csr.simple_csrs) > 1:
            for i in range(len(csr.simple_csrs)):
                (start, length, name) = self.sub_csr_bit_range(csr, i)
                sub_name = self.name.upper() + "_" + name
                bits_str = "Bits {}-{} of `{}`.".format(start, start+length, full_name)
                if atomic_write:
                    if i == (range(len(csr.simple_csrs))-1):
                        bits_str += "Writing this register triggers an update of " + full_name
                    else:
                        bits_str += "The value won't take effect until `" + full_name + "0` is written."
                if i == 0:
                    d = description
                    if description is None:
                        d = bits_str
                    else:
                        d = bits_str + " " + d
                    self.csrs.append(DocumentedCSR(
                        sub_name, self.current_address, short_name=csr.name.upper(), reset=(reset>>start)&((2**length)-1),
                        offset=start,
                        description=d, fields=self.split_fields(fields, start, start + length)
                    ))
                else:
                    self.csrs.append(DocumentedCSR(
                        sub_name, self.current_address, short_name=csr.name.upper(), reset=(reset>>start)&((2**length)-1),
                        offset=start,
                        description=bits_str, fields=self.split_fields(fields, start, start + length)
                    ))
                self.current_address += 4
        else:
            self.csrs.append(DocumentedCSR(
                full_name, self.current_address, short_name=csr.name.upper(), reset=reset,
                description=description, fields=fields
            ))
            self.current_address += 4

    def make_value_table(self, values):
        ret = ""
        max_value_width=len("Value")
        max_description_width=len("Description")
        for v in values:
            (value, name, description) = (None, None, None)
            if len(v) == 2:
                (value, description) = v
            elif len(v) == 3:
                (value, name, description) = v
            else:
                raise ValueError("Unexpected length of CSRField's value tuple")

            max_value_width = max(max_value_width, len(value))
            for d in description.splitlines():
                max_description_width = max(max_description_width, len(d))
        ret += "\n"
        ret += "+-" + "-"*max_value_width + "-+-" + "-"*max_description_width + "-+\n"
        ret += "| " + "Value".ljust(max_value_width) + " | " + "Description".ljust(max_description_width) + " |\n"
        ret += "+=" + "="*max_value_width + "=+=" +  "="*max_description_width + "=+\n"
        for v in values:
            (value, name, description) = (None, None, None)
            if len(v) == 2:
                (value, description) = v
            elif len(v) == 3:
                (value, name, description) = v
            else:
                raise ValueError("Unexpected length of CSRField's value tuple")
            value = value.ljust(max_value_width)
            first_line = True
            for d in description.splitlines():
                if first_line:
                    ret += "| {} | {} |\n".format(value, d.ljust(max_description_width))
                    first_line = False
                else:
                    ret += "| {} | {} |\n".format(" ".ljust(max_value_width), d.ljust(max_description_width))
            ret += "+-" + "-"*max_value_width + "-+-" + "-"*max_description_width + "-+\n"
        return ret

    def print_region(self, stream):
        for csr in self.csrs:
            print("{}".format(csr.name), file=stream)
            print("^" * len(csr.name), file=stream)
            print("", file=stream)
            print("**Address: 0x{:08x} + 0x{:x} = 0x{:08x}**".format(self.origin, csr.address - self.origin, csr.address), file=stream)
            print("", file=stream)
            if csr.description is not None:
                print("    {}".format(csr.description), file=stream)
            self.print_reg(csr, stream)
            if len(csr.fields) > 0:
                max_field_width=len("Field")
                max_name_width=len("Name")
                max_description_width=len("Description")
                value_tables = {}

                for f in csr.fields:
                    max_field_width = max(max_field_width, len("[{}:{}]".format(f.offset + f.size, f.offset)))
                    max_name_width = max(max_name_width, len(f.name))
                    for d in f.description.splitlines():
                        max_description_width = max(max_description_width, len(d))
                    if f.values is not None:
                        value_tables[f.name] = self.make_value_table(f.values)
                        for d in value_tables[f.name].splitlines():
                            max_description_width = max(max_description_width, len(d))
                print("", file=stream)
                print("+-" + "-"*max_field_width + "-+-" + "-"*max_name_width + "-+-" + "-"*max_description_width + "-+", file=stream)
                print("| " + "Field".ljust(max_field_width) + " | " + "Name".ljust(max_name_width) + " | " + "Description".ljust(max_description_width) + " |", file=stream)
                print("+=" + "="*max_field_width + "=+=" + "="*max_name_width + "=+=" + "="*max_description_width + "=+", file=stream)
                for f in csr.fields:
                    field = "[{}:{}]".format(f.offset + f.size, f.offset).ljust(max_field_width)
                    name = f.name.upper().ljust(max_name_width)
                    description = f.description
                    if f.name in value_tables:
                        description += "\n" + value_tables[f.name]

                    first_line = True
                    for d in description.splitlines():
                        if first_line:
                            print("| {} | {} | {} |".format(field, name, d.ljust(max_description_width)), file=stream)
                            first_line = False
                        else:
                            print("| {} | {} | {} |".format(" ".ljust(max_field_width), " ".ljust(max_name_width), d.ljust(max_description_width)), file=stream)
                    print("+-" + "-"*max_field_width + "-+-" + "-"*max_name_width + "-+-" + "-"*max_description_width + "-+", file=stream)
            print("", file=stream)


def generate_docs(soc, base_dir):
    documented_regions = []
    regions = soc.get_csr_regions()
    for csr_region in regions:
        documented_regions.append(DocumentedCSRRegion(csr_region))

    with open(base_dir + "index.rst", "w", encoding="utf-8") as index:
        print(""".. foboot documentation master file, created by
   sphinx-quickstart on Thu Sep 19 09:37:13 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to foboot's documentation!
==================================

.. toctree::
    :hidden:
""", file=index)
        for region in documented_regions:
            print("    {}".format(region.name), file=index)

        print("""
Register Groups
===============
""", file=index)
        for region in documented_regions:
            print("* :doc:`{} <{}>`".format(region.name.upper(), region.name), file=index)

        print("""
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
""", file=index)

    for region in documented_regions:
        with open(base_dir + region.name + ".rst", "w", encoding="utf-8") as outfile:
            region.print_region(outfile)
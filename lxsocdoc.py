#!/usr/bin/env python3
# This variable defines all the external programs that this module
# relies on.  lxbuildenv reads this variable in order to ensure
# the build will finish without exiting due to missing third-party
# programs.
LX_DEPENDENCIES = ["riscv", "icestorm", "nextpnr-ice40"]

# Import lxbuildenv to integrate the deps/ directory
import lxbuildenv

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

    def print_reg(self, reg):
        print("")
        print("    .. wavedrom::")
        print("        :caption: {}".format(reg.name))
        print("")
        print("        {")
        print("            \"reg\": [")
        if len(reg.fields) > 0:
            bit_offset = 0
            for field in reg.fields:
                term=","
                if bit_offset + field.size == self.busword:
                    term=""
                print("                {\"name\": \"" + field.name + "\",  \"bits\": " + str(field.size) + "}" + term)
            bit_offset += field.size
            if bit_offset != self.busword:
                print("                {\"bits\": " + str(self.busword - bit_offset) + "}")
        else:
            print("                {\"name\": \"" + reg.short_name + "[" + str(reg.offset + reg.size - 1) + ":" + str(reg.offset) + "]\",  \"bits\": " + str(reg.size) + "}")
        print("            ], \"config\": {\"hspace\": 400, \"bits\": " + str(self.busword) + ", \"lanes\": 1 }, \"options\": {\"hspace\": 400, \"bits\": " + str(self.busword) + ", \"lanes\": 1}")
        print("        }")
        print("")

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

    def __init__(self, csr_region):
        (self.name, self.origin, self.busword, self.raw_csrs) = csr_region
        self.current_address = self.origin
        self.csrs = []

        for csr in self.raw_csrs:
            self.document_csr(csr)
            # if isinstance(o, _CompoundCSR) and len(o.simple_csrs) > 1:
            #     for sc in o.simple_csrs:
            #         print("    {} / {} - {}".format(sc.name, sc.size, sc))
            # else:
            #     print("    {} / {}: {} - {}".format(o.name, o.size, o.description, o))
            #     if hasattr(o, "fields"):
            #         for f in o.fields.fields:
            #             print("        [{}:{}]: {}    {}".format(f.offset, f.offset + f.size, f.name.upper(), f.description))
        for csr in self.csrs:
            print("{}".format(csr.name))
            print("^" * len(csr.name))
            print("")
            print("**Address: 0x{:08x} + 0x{:x} = 0x{:08x}**".format(self.origin, csr.address - self.origin, csr.address))
            print("")
            if csr.description is not None:
                print("    {}".format(csr.description))
            self.print_reg(csr)
            if len(csr.fields) > 0:
                print("")
                print("    .. list-table:: {}: Field descriptions".format(csr.name))
                print("        :widths: 15 10 100")
                print("        :header-rows: 1")
                print("")
                print("        * - Field")
                print("          - Name")
                print("          - Description")
                for f in csr.fields:
                    print("        * - [{}:{}]".format(f.offset + f.size, f.offset))
                    print("          - {}".format(f.name.upper()))
                    print("          - {}".format(f.description))
            print("")


def generate_docs(soc):
    docs = []
    regions = soc.get_csr_regions()
    for csr_region in regions:
        docs.append(DocumentedCSRRegion(csr_region))

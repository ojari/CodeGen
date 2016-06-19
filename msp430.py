#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OStruct, OMacro, OArg, PRIVATE
from codegen import write_file, write_file_n
from parseOrg import ParseOrg
from config import Spi, Port
import codegen as gen

PATH = "../msp430/"
#PATH = "tmp/"

class Int(OArg):
    def __init__(self, name):
        OArg.__init__(self, name, "int")


class Byte(OArg):
    def __init__(self, name):
        OArg.__init__(self, name, "byte")


def gen_class(cname, attribs, methods):
    c = OClass(cname)
    s = OStruct(cname)
    cargs = []
    ccode = []
    tname = cname+"_t"
    for name, tpe in attribs:
        if name[0]=="-":
            name = name[1:]
        else:
            cargs.append(OArg(name, tpe))
            ccode.append("self->"+name+" = "+name+";")
        s << OArg(name,tpe)
                        
    for mname, args, tpe in methods:
        if mname == "init":
            args = cargs
        args = [OArg("*self", tname)] + args
        m = OMethod(mname, tpe, args)
        if mname == "init":
            for cl in ccode:
                m << cl
        if mname.startswith("_"):
            m = OMethod(mname[1:], "void", args, mods={PRIVATE})
        c << m
    write_file(c, PATH)


# Read MSP430 pin configuration from text file and generate macros to access output pins.
#
p = ParseOrg("launchpad.org")
#sc = OClass("port_sim")


c = Port()
gen.handleExports(c)

spi = Spi()
gen.handleExports(spi)

for i in [1, 2]:
    pdir = []
    pname = "P"+str(i)
    for bit, direction, name in p.parse()[1:]:
        bname = "BIT"+str(bit)
        if direction in ["OUT", "IN/OUT"]:
            c << OMacro("set_"+name, pname+"OUT |= "+bname)
            c << OMacro("clr_"+name, pname+"OUT &= ~"+bname)
            c << OMacro("toggle_"+name, pname+"OUT ^= "+bname)
            pdir.append(bname)

            c.add(name,
                  pname+"OUT |= "+bname,
                  pname+"OUT &= ~"+bname)

            #sc << OMacro("set_"+name,    "bit_set(\""+name+"\")")
            #sc << OMacro("clr_"+name,    "bit_clr(\""+name+"\")")
            #sc << OMacro("toggle_"+name, "bit_toggle(\""+name+"\")")

        if direction in ["IN", "IN/OUT"]:
            c.add_in(name, "((" + pname + "IN & " + bname + ") == " + bname + ")")

            c.sm.add("PIN_"+name, [pname + "DIR &= ~" + bname + ";",
                                   "if (out)",
                                   "{",
                                   pname + "DIR |= " + bname + ";",
                                   "}"])
        if direction in ["IN/OUT"]:
            c << OMacro("get_"+name, "("+pname+"IN & "+bname+") == "+bname)
            c << OMacro("out_"+name, pname+"DIR |= "+bname)
            c << OMacro("in_"+name,  pname+"DIR &= ~"+bname)
            
    if len(pdir) > 0:
        c.m << pname+"DIR = " + (" + ".join(pdir)) + ";"

write_file_n(PATH+"config", c, spi)
#write_file(sc, PATH)

if 0:
    # Generate some template classes
    #
    gen_class("ow", [["init", []],
                 ["reset", []],
                 ["read", []],
                 ["_readByte", [Byte('val')]],
                 ["_writeByte", [Byte('val')]],
                 ])

    gen_class("hd44", [["init", []],
                   ["clear", []],
                   ["goto", [Int("x"), Int("y")]],
                   ["print", [Int("ch")]],
                   ["_command", [Int("cmd")]],
                   ])

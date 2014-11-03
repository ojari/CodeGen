#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OCFile, OStruct, OMacro, OArg, PRIVATE
from parseOrg import ParseOrg
from config import Config

#PATH="../msp430/"
PATH = "../ha/"


def writeFile(c):
    f = OCFile(c.name, PATH, includes=["hw.h"])
    c.genC(f)
    f.close()


def writeFile2(c1, c2):
    f = OCFile(c1.name, PATH, includes=["hw.h"])
    c1.genC(f)
    c2.genC(f)
    f.close()


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
    writeFile(c)


# Read MSP430 pin configuration from text file and generate macros to access output pins.
#
p = ParseOrg("launchpad.org")
cfg = Config()
sc = OClass("port_sim")

for i in [1, 2]:
    pdir = []
    pname = "P"+str(i)
    for bit, direction, name in p.parse()[1:]:
        bname = "BIT"+str(bit)
        if direction in ["OUT", "IN/OUT"]:
            cfg.c << OMacro("set_"+name, pname+"OUT |= "+bname)
            cfg.c << OMacro("clr_"+name, pname+"OUT &= ~"+bname)
            cfg.c << OMacro("toggle_"+name, pname+"OUT ^= "+bname)
            pdir.append(bname)

            cfg.add(name,
                  pname+"OUT |= "+bname,
                  pname+"OUT &= ~"+bname)

            sc << OMacro("set_"+name,    "bit_set(\""+name+"\")")
            sc << OMacro("clr_"+name,    "bit_clr(\""+name+"\")")
            sc << OMacro("toggle_"+name, "bit_toggle(\""+name+"\")")

        if direction in ["IN", "IN/OUT"]:
            cfg.add_in(name, "((" + pname + "IN & " + bname + ") == " + bname + ")")

            cfg.sm.add(name, [pname + "DIR &= ~" + bname + ";",
                              "if (out)",
                              "{",
                              pname + "DIR |= " + bname + ";",
                              "}"])
        if direction in ["IN/OUT"]:
            cfg.c << OMacro("get_"+name, "("+pname+"IN & "+bname+") == "+bname)
            cfg.c << OMacro("out_"+name, pname+"DIR |= "+bname)
            cfg.c << OMacro("in_"+name,  pname+"DIR &= ~"+bname)
            
    if len(pdir) > 0:
        cfg.m << pname+"DIR = " + (" + ".join(pdir)) + ";"

cfg.mr << "return ret;"
writeFile(cfg.c)
exit(0)

writeFile(sc)

gen_class("fifo", 
          [["bufPtr", "void*"],
           ["bufSize", "size_t"],
           ["recSize", "size_t"],
           ["-pushPtr", "void*"],
           ["-popPtr",  "void*"]],
          [["init", [], "void"],
           ["push", [OArg("data", "void*")], "void"],
           ["pop",  [], "void*"]
           ])


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

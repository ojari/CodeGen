#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OCFile, OMacro, OArg, PRIVATE
from parseOrg import ParseOrg

def writeFile(c):
    f = OCFile(c.name, "../msp430/", includes=["<msp430.h>"])
    c.genC(f)
    f.close()


class Int(OArg):
    def __init__(self, name):
        OArg.__init__(self, name, "int")

class Byte(OArg):
    def __init__(self, name):
        OArg.__init__(self, name, "byte")


def gen_class(cname, methods):
    c = OClass(cname)
    for mname, args in methods:
        m = OMethod(mname, "void", args)
        if mname.startswith("_"):
            m = OMethod(mname[1:], "void", args, mods={PRIVATE})
        c << m
    writeFile(c)


# Read MSP430 pin configuration from text file and generate macros to access output pins.
#
p = ParseOrg("launchpad.org")
c = OClass("port")
m = OMethod("init", "void")
c << m
for i in [1,2]:
    pdir = []
    pname = "P"+str(i)
    for bit,direction,name in p.parse()[1:]:
        bname = "BIT"+str(bit)
        if direction in ["OUT", "IN/OUT"]:
            c << OMacro("set_"+name, pname+"OUT |= "+bname)
            c << OMacro("clr_"+name, pname+"OUT &= ~"+bname)
            c << OMacro("toggle_"+name, pname+"OUT ^= "+bname)
            pdir.append(bname)
        if direction in ["IN/OUT"]:
            c << OMacro("get_"+name, "("+pname+"IN & "+bname+") == "+bname)
            c << OMacro("out_"+name, pname+"DIR |= "+bname)
            c << OMacro("in_"+name,  pname+"DIR &= ~"+bname)
            
    if len(pdir) > 0:
        m << pname+"DIR = " + (" + ".join(pdir)) + ";"
writeFile(c)
exit(0)

# Generate some template classes
#
gen_class("ow", [[ "init", []],
                 [ "reset", []],
                 [ "read", []],
                 [ "_readByte", [Byte('val')]],
                 [ "_writeByte", [Byte('val')]],
             ])

gen_class("hd44", [[ "init", []],
                   [ "clear", []],
                   [ "goto", [Int("x"), Int("y")]],
                   [ "print", [Int("ch")]],
                   [ "_command", [Int("cmd")]],
               ])

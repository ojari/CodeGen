#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OCFile, OMacro, OArg, PRIVATE
from parseOrg import ParseOrg

def writeFile(c):
    f = OCFile(c.name, "../msp430")
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
c = OClass("config")
for i in [1,2]:
    for bit,direction,name in p.parse()[1:]:
        if direction == "OUT":
            c << OMacro("set_"+name, "P"+str(i)+"OUT |= BIT"+str(bit))
            c << OMacro("clr_"+name, "P"+str(i)+"OUT &= ~BIT"+ str(bit))
            c << OMacro("toggle_"+name, "P"+str(i)+"OUT ^= BIT"+ str(bit))
writeFile(c)


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

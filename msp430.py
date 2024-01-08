#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OStruct, OMacro, OArg, PRIVATE, OEmptyLine
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

def bitRead(pin, reg):
    return "((" + pin.port_name() + reg + " & " + pin.bit_name() + ") == " + pin.bit_name() + ")"

def bitSet(pin, reg):
    return pin.port_name() + reg + " |= "  + pin.bit_name()

def bitClr(pin, reg):
    return pin.port_name() + reg + " &= ~" + pin.bit_name()

def bitTgl(pin, reg):
    return pin.port_name() + reg + " ^= "  + pin.bit_name()

class PinDef:
    def __init__(self, row):
        self.port = row[0][0]
        self.pin = row[0][2]
        self.af = row[1].strip()
        self.direction = row[2]
        self.name = row[3]

    def port_name(self):
        return "P" + self.port

    def bit_name(self):
        return "BIT" + self.pin

    def reg(self, reg):
        pass

# Read MSP430 pin configuration from text file and generate macros to access output pins.
#
org = ParseOrg("launchpad.org")
org.parse()

c = Port()
gen.handleExports(c)

spi = Spi()
gen.handleExports(spi)

table = org.items[0].items[0]
tablePins = [PinDef(x) for x in table[1:] if len(x[2]) > 0]

c << OEmptyLine()
for pin in tablePins:
    if pin.direction in ["OUT", "IN/OUT"]:
        c << OMacro("set_"+pin.name, bitSet(pin, "OUT"))
        c << OMacro("clr_"+pin.name, bitClr(pin, "OUT"))
        c << OMacro("tgl_"+pin.name, bitTgl(pin, "OUT"))
        c << OEmptyLine()

    if pin.direction in ["IN/OUT"]:
        c << OMacro("get_"+pin.name, bitRead(pin, "IN"))
        c << OMacro("out_"+pin.name, bitSet(pin, "DIR"))
        c << OMacro("in_"+pin.name,  bitClr(pin, "DIR"))
        c << OEmptyLine()


for pin in tablePins:
    if pin.direction in ["OUT", "IN/OUT"]:
        #pdir.append(bname)

        c.add(pin.name, bitSet(pin, "OUT"), bitClr(pin, "OUT"))
    if pin.direction in ["IN", "IN/OUT"]:
        c.add_in(pin.name, bitRead(pin, "IN"))

        c.sm.add("PIN_"+pin.name, [bitClr(pin, "DIR") + ";",
                                "if (out)",
                                "{",
                                bitSet(pin, "DIR") + ";",
                                "}"])
        
if 1:
    for port in ["1", "2"]:
        items = [pin.bit_name() for pin in tablePins if pin.port == port and ("OUT" in pin.direction)]
        c.m << "P"+port+"DIR = " + ("|".join(items)) + ";"

write_file_n(PATH+"config", c, spi)

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

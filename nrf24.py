from parseOrg import ParseOrg
import codegen as gen
import re

FILENAME = "c:/home/mbed/blinky/nrf24reg.org"
MODULE = "NRF24"

def maskByte(val):
    high, low = val.split(":")
    val = 0
    for i in range(int(low), int(high)+1):
        val += 1 << i
    return hex(val)

def validName(name):
    name = name.strip()
    name = name.replace("-", "m")
    return name

def toName(*list):
    return MODULE + "_" + ("_".join(list))

class Row:
    def __init__(self, line):
        self.name = line[1]
        self.mode = line[2]
        self.desc = line[4]

class Bit(Row):
    def __init__(self, line, reg):
        Row.__init__(self, line)
        self.bit = line[3]
        self.reg = reg
        self.enumName = None

    def isOneBit(self):
        return (not ":" in self.bit)

    def bitOffset(self):
        if self.isOneBit():
            return 0
        high, low = self.bit.split(":")
        return int(low)

    def getName(self):
        if self.isOneBit():
            return toName(self.reg.name, self.name)
        else:
            return toName(self.reg.name, self.name, "MASK")

    def getMacro(self):
        if self.isOneBit():
            return gen.OMacro(self.getName(), "(1<<" + self.bit + ")")
        else:
            return gen.OMacro(self.getName(), maskByte(self.bit))

    def handleList(self, lst):
        #ret = []
        value = 0
        self.enumName = toName(self.reg.name, self.name, "T")
        enum = gen.OEnum(self.enumName, {})
        for item in lst:
            if item == "-":
                value += 1
                continue
            enum.add(toName(self.reg.name, self.name, validName(item)) + " = " + str(value))
            #ret.append( gen.OMacro([MODULE, "VAL", self.reg.name, self.name, validName(item)], str(value)) )
            value += 1
        #return ret
        return enum

class Register(Row):
    def __init__(self, line):
        Row.__init__(self, line)
        self.adr = line[0]
        self.bits = []

    def isValid(self):
        items = [x for x in self.bits if len(x.mode)>0]
        return (len(items) > 0) or (len(self.mode) > 0)

    def getName(self):
        return toName(reg.name)

    def add(self, line):
        self.bits.append(Bit(line, self))

class Command:
    def __init__(self, line):
        self.name = line[0]
        code = line[1].replace("A", "0")
        self.code = int("0b" + code.replace("P", "0"), 2)
        self.action = line[2].strip()

    def getName(self):
        return toName("CMD", self.name)
        

#-------------------------------------------------------------------------------
def FunctionName(reg, bit):
    name = reg.name.lower()
    if bit.name != "DATA":
        name += ("_" + bit.name.lower())
    return name

def GenSetRegister(reg, bit):
    tpe = "uint8_t"
    if bit.enumName:
        tpe = bit.enumName
    m = gen.OMethod("set_" + FunctionName(reg, bit), "void",
                    [gen.OArg("value", tpe)])
    m.doc = "Set " + bit.desc
    m << "int reg;"
    m << ""
    m << "reg = nrf24_readReg("+reg.getName()+");"
    if bit.isOneBit():
        m << gen.IF("value",
                    ["reg |= " + bit.getName() + ";"])
        m << gen.ELSE(
                    ["reg &= (~" + bit.getName() + ");"])
    else:
        m << "reg &= (~" + bit.getName() + ");"
        offset = bit.bitOffset()
        if offset:
            m << "reg |= (value << "+str(offset)+");"
        else:
            m << "reg |= value;"
    m << "nrf24_writeReg("+reg.getName()+", reg);"
    return m
    
def GenGetRegister(reg, bit):
    m = gen.OMethod("get_" + FunctionName(reg, bit), "uint8_t",
                    [])
    m.doc = "Get " + bit.desc
    m.setCode("""
    int reg;
    reg = nrf24_readReg({0});
    return reg & {1};""".format(reg.getName(), bit.getName()))
    return m

def GenWriteReg():
    m = gen.OMethod("writeReg", "void", 
                    [gen.OArg("reg", "uint8_t"), gen.OArg("val", "uint8_t")],
                    {gen.PUBLIC, gen.EXTERNAL})
    m.doc = "Set nRF register value"
    return m

def GenReadReg():
    m = gen.OMethod("readReg", "uint8_t", 
                    [gen.OArg("reg", "uint8_t")],
                    {gen.PUBLIC, gen.EXTERNAL})
    m.doc = "Get nRF register value"
    m.setCode("""
    int val = 0x00;
    
    return val;""")
    return m

def GenCmd(cmd):
    retType = "uint8_t"
    args = [gen.OArg("arg"+str(number), "uint8_t") for number in range(0,int(cmd.action))]

    argsCall = ", ".join([cmd.getName()] + [arg.name for arg in args])

    if len(args) > 0:
        retType = "uint32_t"

    m = gen.OMethod("cmd_" + cmd.name.lower(), retType, 
                    args)
    m.doc = "Send command " + cmd.name
    m << "return nrf24_command" + str(len(args)) + "(" + argsCall + ");"
    return m
    
def GenCommand0():
    m = gen.OMethod("command0", "uint8_t", 
                    [gen.OArg("cmd", "uint8_t")],
                    {gen.PUBLIC, gen.EXTERNAL})
    m.doc = "Send command with zero arguments."
    return m


def GenCommand3():
    m = gen.OMethod("command3", "uint32_t", 
                    [gen.OArg("cmd", "uint8_t"), 
                     gen.OArg("arg1", "uint8_t"),
                     gen.OArg("arg2", "uint8_t"),
                     gen.OArg("arg3", "uint8_t")],
                    {gen.PUBLIC, gen.EXTERNAL})
    m.doc = "Send command with three arguments."
    return m

p = ParseOrg(FILENAME)
p.parse()

# Parse table to Register and Row classes
#
registers = []
reg = None
for rowLine in p.items[0].items[0][1:]:
    if rowLine[0]:
        if reg:
            registers.append(reg)
        reg = Register(rowLine)
    else:
        reg.add(rowLine)

commands = []
for cmdLine in p.items[1].items[0][1:]:
    cmd = Command(cmdLine)
    if cmd.action:
        commands.append(cmd)

# Generate code
#
nrf = gen.OClass("nrf24")
comp1 = re.compile(".*\{(.*)\}.*")
comp2 = re.compile(".*\[(.*)\].*")
for reg in registers:
    if not reg.isValid():
        continue
    nrf << gen.OMacro(reg.getName(), "0x"+reg.adr)
    for bit in reg.bits:
        nrf << bit.getMacro()
        m = comp2.match(bit.desc)
        if m:
            nrf << bit.handleList(eval("["+m.group(1)+"]"))
        else:
            m = comp1.match(bit.desc)
            if m:
                nrf << bit.handleList(m.group(1).split(","))
    nrf << gen.OEmptyLine()

for cmd in commands:
    nrf << gen.OMacro(cmd.getName(), hex(cmd.code))
nrf << gen.OEmptyLine()

module = MODULE.lower()

for reg in registers:
    if "g" in reg.mode:
        mname = ["get", reg.name.lower()]
        m = gen.OMethod("_".join(mname), "uint32_t")
        m.doc = "Get register " + reg.desc
        m << "return nrf24_readReg("+reg.getName()+");"
        nrf << m
    if "s" in reg.mode:
        mname = ["set", reg.name.lower()]
        m = gen.OMethod("_".join(mname), "void", [gen.OArg("val", "uint8_t")])
        m.doc = "Set register " + reg.desc
        m << "nrf24_writeReg("+reg.getName()+", val);"
        nrf << m
    for bit in reg.bits:
        if "s" in bit.mode:
            nrf << GenSetRegister(reg, bit)

        if "g" in bit.mode:
            nrf << GenGetRegister(reg, bit)

for cmd in commands:
    if cmd.action in ["3"]:
        nrf << GenCmd(cmd)

nrf << GenWriteReg()
nrf << GenReadReg()
nrf << GenCommand0()
nrf << GenCommand3()

gen.write_file_n("c:/home/ti/workspace/Example_Spi/nrf24", nrf)
print("Done.")

#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OCFile, OStruct, OMacro, OArg, PRIVATE, OSwitch
from parseOrg import ParseOrg

def writeFile(c):
    f = OCFile(c.name, "../stm32/",
               includes = ["stm32f0xx.h"])
    c.genC(f)
    f.close()

def writeFile2(c1,c2):
    f = OCFile(c1.name, "../stm32/")
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
    writeFile2(s, c)


# Read STM32 pin configuration from text file and generate macros to access output pins.
#
p = ParseOrg("stm32.org")
c = OClass("config")
m = OMethod("port_init", "void")
c << m

ms = OMethod("port_set", "void", [OArg("pin", "uint8_t")] )
ss = OSwitch("pin")
ms << ss
c << ms

mc = OMethod("port_clear", "void", [OArg("pin", "uint8_t")] )
sc = OSwitch("pin")
mc << sc
c << mc

m << "GPIO_InitTypeDef ioInit;"

pins = []
for i in ['A','B','C']:
    pout = []
    pin  = []
    paf  = []
    for bit,af,desc,direction in p.parse()[1:]:
        af = af.strip()
        print "AF:",af,len(af)
        if len(af) > 0:
            paf.append("GPIO_Pin_"+bit)
            continue
        if direction in ["OUT", "IN/OUT"]:
            c << OMacro("set_"+desc,    "GPIO"+i+"->BSRR = GPIO_Pin_"+bit)
            c << OMacro("clr_"+desc,    "GPIO"+i+"->BRR  = GPIO_Pin_"+bit)
            #c << OMacro("toggle_"+name, "P"+str(i)+"OUT ^= BIT"+ str(bit))

            pout.append("GPIO_Pin_"+bit)
            pins.append([direction,desc,i,bit])
        if direction in ["IN", "IN/OUT"]:
            #c << OMacro("get_"+name,   "("+pname+"IN & BIT"+str(bit)+" == BIT"+str(bit)+")")
            #c << OMacro("in_"+name,    pname+"DIR &= ~BIT"+ str(bit))
            #c << OMacro("out_"+name,   pname+"DIR |= BIT"+ str(bit))
            pin.append("GPIO_Pin_"+bit)
            if direction != "IN/OUT":
                pins.append([direction,desc,i,bit])

    if len(pout) > 0 or len(pin) > 0:
        m << ""
        m << "RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIO"+i+", ENABLE);"
            
    if len(pout) > 0:
        m << ""
        m << "ioInit.GPIO_Pin = " + (" | ".join(pout)) + ";"
        m << "ioInit.GPIO_Mode = GPIO_Mode_OUT;"
        m << "ioInit.GPIO_OType = GPIO_OType_PP;"
        m << "ioInit.GPIO_PuPd = GPIO_PuPd_NOPULL;"
        m << "ioInit.GPIO_Speed = GPIO_Speed_10MHz;"
        m << "GPIO_Init(GPIO"+i+", &ioInit);"
    if len(pin) > 0:
        m << ""
        m << "ioInit.GPIO_Pin = " + (" | ".join(pin)) + ";"
        m << "ioInit.GPIO_Mode = GPIO_Mode_IN;"
        m << "ioInit.GPIO_OType = GPIO_OType_PP;"
        m << "ioInit.GPIO_PuPd = GPIO_PuPd_DOWN;"
        m << "ioInit.GPIO_Speed = GPIO_Speed_10MHz;"
        m << "GPIO_Init(GPIO"+i+", &ioInit);"
    if len(paf) > 0:
        m << ""
        m << "ioInit.GPIO_Pin = " + (" | ".join(paf)) + ";"
        m << "ioInit.GPIO_Mode = GPIO_Mode_AF;"
        #m << "ioInit.GPIO_OType = GPIO_OType_PP;"
        #m << "ioInit.GPIO_PuPd = GPIO_PuPd_DOWN;"
        m << "ioInit.GPIO_Speed = GPIO_Speed_10MHz;"
        m << "GPIO_Init(GPIO"+i+", &ioInit);"
        m << ""
        for item in paf:
            psource = "GPIO_PinSource"+item[len("GPIO_Pin_"):]
            m << "GPIO_PinAFConfig(GPIO"+i+", "+psource+", 1);"

pinId = 1
for direction,desc,port,bit in pins:
    name = "PIN_"+desc
    c << OMacro(name, str(pinId))
    ss.add(name, ["GPIO"+port+"->BSRR = GPIO_Pin_"+bit+";"])

    sc.add(name, ["GPIO"+port+"->BRR = GPIO_Pin_"+bit+";"])
    pinId += 1


writeFile(c)


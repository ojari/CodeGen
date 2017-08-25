#
# Copyright 2014-5 Jari Ojanen
#
from codegen import OClass, OMethod, OStruct, OMacro, OArg, OSwitch
from codegen import write_file_n
from parseOrg import ParseOrg
from config import Spi, Port
import codegen as gen

#FILENAME = "stm32.org"
FILENAME = "nucleom7.org"

class PinDef:
    def __init__(self, row):
        self.port = row[0][0]
        self.pin = row[0][1:]
        self.af = row[1].strip()
        self.desc = row[2]
        self.direction = row[3]

    def macro(self, func, reg):
        return OMacro(func+"_"+self.desc, "GPIO"+self.port+"->"+reg+" GPIO_Pin_"+self.pin)

    def pin_name(self):
        return "GPIO_Pin_" + self.pin

    def reg(self, reg):
        return "GPIO" + self.port + "->" + reg

# Read STM32 pin configuration from text file and generate macros to access output pins.
#
p = ParseOrg(FILENAME)


c = Port()
gen.handleExports(c)

spi = Spi()
gen.handleExports(spi)

c.m << "GPIO_InitTypeDef ioInit;"

p.parse()
table = p.items[0].items[0]
table2 = [PinDef(x) for x in table[1:] if len(x[2]) > 0 and x[2][0] != "["]

ports = list(set([pin.port for pin in table2]))  # all unique ports in the pins
ports.sort()

pins = []
for portName in ports:
    pout = []
    pin = []
    paf = []
    pinDefs = [x for x in table2 if x.port == portName]

    if pinDefs:
        c.m << ""
        c.m << "__HAL_RCC_GPIO" + portName + "_CLK_ENABLE();"
    
    for pindef in pinDefs:
        if len(pindef.af) > 0:
            paf.append(pindef)
            continue
        if pindef.direction in ["OUT", "IN/OUT"]:
            c << pindef.macro("set", "BSRR =")
            c << pindef.macro("clr", "BRR =")
            c << pindef.macro("toggle", "ODR ^=")

            pout.append(pindef.pin_name())
            pins.append(pindef)
        if pindef.direction in ["IN"]:
            #c << OMacro("get_"+name,   "("+pname+"IN & BIT"+str(bit)+" == BIT"+str(bit)+")")
            #c << OMacro("in_"+name,    pname+"DIR &= ~BIT"+ str(bit))
            #c << OMacro("out_"+name,   pname+"DIR |= BIT"+ str(bit))
            pin.append(pindef.pin_name())
            pins.append(pindef)

    if pout:
        c.m << ""
        c.m << "ioInit.GPIO_Pin = " + (" | ".join(pout)) + ";"
        c.m << "ioInit.GPIO_Mode = GPIO_Mode_OUT;"
        c.m << "ioInit.GPIO_OType = GPIO_OType_PP;"
        c.m << "ioInit.GPIO_PuPd = GPIO_PuPd_NOPULL;"
        c.m << "ioInit.GPIO_Speed = GPIO_Speed_10MHz;"
        c.m << "GPIO_Init(GPIO"+pindef.port+", &ioInit);"
    if pin:
        c.m << ""
        c.m << "ioInit.GPIO_Pin = " + (" | ".join(pin)) + ";"
        c.m << "ioInit.GPIO_Mode = GPIO_Mode_IN;"
        c.m << "ioInit.GPIO_OType = GPIO_OType_PP;"
        c.m << "ioInit.GPIO_PuPd = GPIO_PuPd_DOWN;"
        c.m << "ioInit.GPIO_Speed = GPIO_Speed_10MHz;"
        c.m << "GPIO_Init(GPIO"+pindef.port+", &ioInit);"
    if paf:
        afpins = ["GPIO_Pin_" + pd.pin for pd in paf]
        c.m << ""
        c.m << "ioInit.GPIO_Pin = " + (" | ".join(afpins)) + ";"
        c.m << "ioInit.GPIO_Mode = GPIO_Mode_AF;"
        #c.m << "ioInit.GPIO_OType = GPIO_OType_PP;"
        #c.m << "ioInit.GPIO_PuPd = GPIO_PuPd_DOWN;"
        c.m << "ioInit.GPIO_Speed = GPIO_Speed_10MHz;"
        c.m << "GPIO_Init(GPIO"+paf[0].port+", &ioInit);"
        c.m << ""
        for pd in paf:
            c.m << "GPIO_PinAFConfig(GPIO"+pd.port+", GPIO_PinSource"+pd.pin+", "+pd.af+");"

pinId = 1
for pd in pins:
    name = "PIN_"+pd.desc

    c.add(pd.desc,
          pd.reg('BSRR')+"= "+pd.pin_name(),
          pd.reg('BRR')+" = "+pd.pin_name())

    if pd.direction == "IN/OUT":
        c.sm.add(name, [pd.reg('MODER')+" &= ~(((uint32_t)0x3) << ("+pd.pin+"*2));",
                        "if (out)",
                        "{",
                        pd.reg('MODER')+" |= (((uint32_t)0x1) << ("+pd.pin+"*2));",
                        "}"])

    if pd.direction in ["IN", "IN/OUT"]:
        c.add_in(pd.desc, "(("+pd.reg('IDR')+" & "+pd.pin_name()+") == "+pd.pin_name()+")")

    pinId += 1

write_file_n(p.vars['PATH']+"/config", c, spi)

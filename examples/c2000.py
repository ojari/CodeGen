#
# Copyright 2017 Jari Ojanen
#
from py2code.codegen import OClass, OMethod, OStruct, OMacro, OArg, OSwitch
from py2code.codegen import write_file_n, handleExports
from py2code.parseOrg import ParserOrg
from py2code.generator import CGenerator, HGenerator
from config import Spi, Port

FILENAME = "examples/c2000.org"
PATH="out"

class PinDef:
    def __init__(self, row):
        self.pin = row[0]
        self.alt = row[1].strip()
        self.desc = row[2].strip()

    def macro(self, func: str, regName) -> OMacro:
        return OMacro(func+"_"+self.desc, "EALLOW; " + self.reg(regName) + " = 1; EDIS")

    def pin_name(self) -> str:
        return "GPIO_Pin_" + self.pin

    def reg(self, reg) -> str:
        rset = 'Data'
        if reg in ["GPADIR"]:
            rset = 'Ctrl'
        return "Gpio"+rset+"Regs."+reg+".bit.GPIO"+self.pin

    def isOut(self) -> bool:
        return self.alt == "OUT"

    def isIn(self) -> bool:
        return self.alt == "IN"

    def isAF(self) -> bool:
        return self.alt == "AF"
    
# Read STM32 pin configuration from text file and generate macros to access output pins.
#
p = ParserOrg(FILENAME)

c = Port()
handleExports(c)

spi = Spi()
handleExports(spi)

c.m << "EALLOW;"

p.parse()
table = p.items[0].items[0]
table2 = [PinDef(x) for x in table.rows[1:] if len(x[2]) > 0 and x[2][0] != "<"]

pins = []
for pindef in table2:
    if pindef.isOut():
        c << pindef.macro("set", "GPASET")
        c << pindef.macro("clr", "GPACLEAR")
        c << pindef.macro("toggle", "GPATOGGLE")

        c.add(pindef.desc,
            pindef.reg('GPASET') + " = 1",
            pindef.reg('GPACLEAR') + " = 1")
        
        c.m << pindef.reg('GPADIR') + ' = 0; // ' + pindef.desc
        c.m << pindef.reg('GPADIR') + ' = 1;'

    elif pindef.isIn():
        #c.add_in(pd.desc, "(("+pd.reg('IDR')+" & "+pd.pin_name()+") == "+pd.pin_name()+")")

        c.m << pindef.reg('GPADIR') + ' = 0;'
        pass

    elif pindef.isAF():
        pass

c.m << "EDIS;"

data = [[f"{PATH}/c2k_hal.h", HGenerator()],
        [f"{PATH}/c2k_hal.c", CGenerator()]] 
write_file_n(data, c.members, spi)

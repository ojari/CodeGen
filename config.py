#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OSwitch, OArg, OMacro, PUBLIC, REMEMBER

BYTE = "uint8_t"

class Config:
    def __init__(self):
        self.pin_id = 1

        self.c = OClass("io")
        self.m = OMethod("init", "void")
        self.c << self.m

        self._ms = OMethod("set", "void", [OArg("pin", BYTE)])
        self._ss = OSwitch("pin")
        self._ms << self._ss
        self.c << self._ms

        self._mc = OMethod("clear", "void", [OArg("pin", BYTE)])
        self._sc = OSwitch("pin")
        self._mc << self._sc
        self.c << self._mc

        self.mm = OMethod("mode", "void", [OArg("pin", BYTE), OArg("out", BYTE)])
        self.sm = OSwitch("pin")
        self.mm << self.sm
        self.c << self.mm

        self.mr = OMethod("read", BYTE, [OArg("pin", BYTE)])
        self.sr = OSwitch("pin")
        self.mr << "uint8_t ret=0;"
        self.mr << self.sr
        self.c << self.mr

        #----------------------------------------------------------------------
        self.cspi = OClass("spi")
        
        self.spi_init = OMethod("init", "void",
                                mods={PUBLIC,REMEMBER})
        self.cspi << self.spi_init

        self.spi_tx = OMethod("tx", "void", [OArg("val", BYTE)],
                              mods={PUBLIC,REMEMBER})
        self.cspi << self.spi_tx

        self.spi_rx = OMethod("rx", BYTE, [OArg("val", BYTE)],
                              mods={PUBLIC,REMEMBER})
        self.cspi << self.spi_rx
        

    def add(self, name, oper_set, oper_clear):
        self._ss.add("PIN_"+name, [oper_set + ";"])
        self._sc.add("PIN_"+name, [oper_clear + ";"])
        self.c << OMacro("PIN_"+name, str(self.pin_id))
        self.pin_id += 1


    def add_in(self, name, oper):
        self.sr.add("PIN_"+name, ["ret = " + oper + ";"])

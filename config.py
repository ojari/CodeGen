#
# Copyright 2014 Jari Ojanen
#
from codegen import OClass, OMethod, OSwitch, OArg, OMacro


class Config:
    def __init__(self):
        self.pin_id = 1

        self.c = OClass("config")
        self.m = OMethod("port_init", "void")
        self.c << self.m

        self._ms = OMethod("port_set", "void", [OArg("pin", "uint8_t")])
        self._ss = OSwitch("pin")
        self._ms << self._ss
        self.c << self._ms

        self._mc = OMethod("port_clear", "void", [OArg("pin", "uint8_t")])
        self._sc = OSwitch("pin")
        self._mc << self._sc
        self.c << self._mc

        self.mm = OMethod("port_mode", "void", [OArg("pin", "uint8_t"), OArg("out", "uint8_t")])
        self.sm = OSwitch("pin")
        self.mm << self.sm
        self.c << self.mm

        self.mr = OMethod("port_read", "uint8_t", [OArg("pin", "uint8_t")])
        self.sr = OSwitch("pin")
        self.mr << "uint8_t ret=0;"
        self.mr << self.sr
        self.c << self.mr

    def add(self, name, oper_set, oper_clear):
        self._ss.add("PIN_"+name, [oper_set + ";"])
        self._sc.add("PIN_"+name, [oper_clear + ";"])
        self.c << OMacro("PIN_"+name, str(self.pin_id))
        self.pin_id += 1

    def add_in(self, name, oper):
        self.sr.add("PIN_"+name, ["ret = " + oper + ";"])
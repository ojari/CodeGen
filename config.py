#
# Copyright 2014-5 Jari Ojanen
#
from codegen import OClass, OMethod, OSwitch, OArg, OMacro, PUBLIC, REMEMBER
from codegen import export, exportclass

BYTE = "uint8_t"
VOID = "void"

@exportclass
class spi(OClass):
    def __init__(self):
        OClass.__init__(self, "spi")

    @export(VOID)
    def init(self, meth):
        meth.mods = {PUBLIC,REMEMBER}
        meth.args = []

    @export(VOID)
    def tx(self, meth):
        meth.mods = {PUBLIC,REMEMBER}
        meth.args = [OArg("val", BYTE)]

    @export(VOID)
    def rx(self, meth):
        meth.mods = {PUBLIC,REMEMBER}
        meth.args = [OArg("val", BYTE)]


@exportclass
class port(OClass):
    def __init__(self):
        OClass.__init__(self, "port")
        self.pin_id = 1

    @export(VOID)
    def init(self, meth):
        self.m = meth

    @export(VOID)
    def set(self, meth):
        meth.args = [OArg("pin", BYTE)]
        self.ss = OSwitch("pin")
        meth << self.ss

    @export(VOID)
    def clear(self, meth):
        meth.args = [OArg("pin", BYTE)]
        self.sc = OSwitch("pin")
        meth << self.sc

    @export(VOID)
    def mode(self, meth):
        meth.args = [OArg("pin", BYTE), OArg("out", BYTE)]
        self.sm = OSwitch("pin")
        meth << self.sm

    @export(BYTE)
    def read(self, meth):
        meth.args = [OArg("pin", BYTE)]
        self.sr = OSwitch("pin")

        meth << "uint8_t ret=0;"
        meth << self.sr

        self.mr = meth

    def add(self, name, oper_set, oper_clear):
        self.ss.add("PIN_"+name, [oper_set + ";"])
        self.sc.add("PIN_"+name, [oper_clear + ";"])
        self << OMacro("PIN_"+name, str(self.pin_id))
        self.pin_id += 1


    def add_in(self, name, oper):
        self.sr.add("PIN_"+name, ["ret = " + oper + ";"])



#
# Copyright 2014-5 Jari Ojanen
#
from codegen import OClass, OMethod, OSwitch, OArg, OMacro, PUBLIC, REMEMBER
from codegen import export, exportclass, CLASSES
from codegen import writeFileN

BYTE = "uint8_t"

@exportclass
class spi(OClass):
    def __init__(self):
        OClass.__init__(self, "spi")

    @export("void")
    def init(self, meth):
        meth.mods = {PUBLIC,REMEMBER}
        meth.args = []

    @export("void")
    def tx(self, meth):
        meth.mods = {PUBLIC,REMEMBER}
        meth.args = [OArg("val", BYTE)]

    @export("void")
    def rx(self, meth):
        meth.mods = {PUBLIC,REMEMBER}
        meth.args = [OArg("val", BYTE)]


@exportclass
class port(OClass):
    def __init__(self):
        OClass.__init__(self, "port")

    @export("void")
    def init(self, meth):
        pass

    @export("void")
    def set(self, meth):
        meth.args = [OArg("pin", BYTE)]
        self.ss = OSwitch("pin")
        meth << self.ss

    @export("void")
    def clear(self, meth):
        meth.args = [OArg("pin", BYTE)]
        self.sc = OSwitch("pin")
        meth << self.sc

    @export("void")
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
    
INSTANCES = []

for c in CLASSES:
    o = c()
    m = [getattr(o,x) for x in dir(o) if "export" in dir(getattr(o,x))]

    for fn in m:
        meth = OMethod(fn.__name__, fn.rtype)
        fn(meth)
        o << meth
    
    INSTANCES.append(o)

#writeFileN("test", "", INSTANCES)
def getInstance(name):
    for i in INSTANCES:
        if i.name == name:
            return i
    return None

    
class Config:
    def __init__(self):
        self.pin_id = 1

        self.obj = getInstance("port")

    def add(self, name, oper_set, oper_clear):
        self.obj.ss.add("PIN_"+name, [oper_set + ";"])
        self.obj.sc.add("PIN_"+name, [oper_clear + ";"])
        self.obj << OMacro("PIN_"+name, str(self.pin_id))
        self.pin_id += 1


    def add_in(self, name, oper):
        self.obj.sr.add("PIN_"+name, ["ret = " + oper + ";"])

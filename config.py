from codegen import OClass,OMethod,OSwitch,OArg

class Config:
    def __init__(self):
        self.c = OClass("config")
        self.m = OMethod("port_init", "void")
        self.c << self.m

        self.ms = OMethod("port_set", "void", [OArg("pin", "uint8_t")] )
        self.ss = OSwitch("pin")
        self.ms << self.ss
        self.c << self.ms

        self.mc = OMethod("port_clear", "void", [OArg("pin", "uint8_t")] )
        self.sc = OSwitch("pin")
        self.mc << self.sc
        self.c << self.mc

        self.mm = OMethod("port_mode", "void", [OArg("pin", "uint8_t"), OArg("out", "uint8_t")] )
        self.sm = OSwitch("pin")
        self.mm << self.sm
        self.c << self.mm

        self.mr = OMethod("port_read", "uint8_t", [OArg("pin", "uint8_t")] )
        self.sr = OSwitch("pin")
        self.mr << "uint8_t ret=0;"
        self.mr << self.sr
        self.c << self.mr

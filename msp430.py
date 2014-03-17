from codegen import OClass, OMethod, OCFile, OArg, PRIVATE


class Int(OArg):
    def __init__(self, name):
        OArg.__init__(self, name, "int")

class Byte(OArg):
    def __init__(self, name):
        OArg.__init__(self, name, "byte")


def gen_class(cname, methods):
    c = OClass(cname)
    for mname, args in methods:
        m = OMethod(mname, "void", args)
        if mname.startswith("_"):
            m = OMethod(mname[1:], "void", args, mods={PRIVATE})
        c << m

    f = OCFile(cname)
    c.genC(f)
    f.close()


gen_class("ow", [[ "init", []],
                 [ "reset", []],
                 [ "read", []],
                 [ "_readByte", [Byte('val')]],
                 [ "_writeByte", [Byte('val')]],
             ])

gen_class("hd44", [[ "init", []],
                   [ "clear", []],
                   [ "goto", [Int("x"), Int("y")]],
                   [ "print", [Int("ch")]],
                   [ "_command", [Int("cmd")]],
               ])

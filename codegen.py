#
# Copyright 2014 Jari Ojanen
#

PRIVATE   = "private"
PROTECTED = "protected"
PUBLIC    = "public"
STATIC    = "static"
TEST      = "test"
GETTER    = "getter"
SETTER    = "setter"
REMEMBER  = "remember"

def q(s):
    return "\""+s+"\""

def writeFile(c, path):
    f = OCFile(c.name, path, includes=["hw.h"])
    c.genC(f)
    f.close()


def writeFileN(fname, path, *classes):
    f = OCFile(fname, path, includes=["hw.h"])
    for c in classes:
        c.genC(f)
    f.close()


class OBlock(object):
    def __init__(self, parent):
        self.parent = parent

    def __enter__(self):
        self.parent << "{"

    def __exit__(self,a,b,c):
        self.parent << "}"

class OFile(object):
    def __init__(self, fname):
        print("generating "+fname+"...")
        self.f = open(fname, "wt")
        self.indent = 0

    def block(self, pre):
        self << pre
        return OBlock(self)

    def __lshift__(self, s):
        if s == "}":
            self.indent -= 1
        #print ("\t"*self.indent) + self.line
        self.f.write(("    "*self.indent) + s + "\n")
        if s == "{" or s.startswith("case "):
            self.indent += 1
        if s == "break;":
            self.indent -= 1

    def addCsIncludes(self, includes):
        for inc in includes:
            self.f.write("using "+inc+";\n")
        self.f.write("\n")

    def close(self):
        self.f.close()


class OCFile(object):
    def __init__(self, fbase, fpath="", includes=[]):
        cExtra = ""
        hExtra = ""
        if "stm32" in fpath:
            cExtra = "src/"
            hExtra = "inc/"
        self.c = OFile(fpath+cExtra+fbase+".c")
        self.h = OFile(fpath+hExtra+fbase+".h")

        self.h << "#ifndef _"+fbase.upper()+"_H"
        self.h << "#define _"+fbase.upper()+"_H"
        self.h << ""

        for inc in includes + [fbase+".h"]:
            if inc.startswith("<"):
                self.c << "#include "+inc
            else:
                self.c << "#include "+q(inc)

    def close(self):
        self.h << ""
        self.h << "#endif"
        self.h.close()
        self.c.close()


class OBase(object):
    def __init__(self, name, ctype, mods):
        self.name = name
        self.ctype = ctype
        self.mods = mods

    def csMods(self):
        visible = {PRIVATE, PROTECTED, PUBLIC, STATIC}
        
        return " ".join(visible.intersection(self.mods)) + " "


class OArg(OBase):
    def __init__(self, name, ctype, mods={PRIVATE}):
        OBase.__init__(self, name, ctype, mods)

    def genC(self, f):
        f.h << self.ctype + " " + self.name + ";"

    def genCS(self, f):
        f << self.csMods() + self.ctype + " " + self.name + ";"

    def argDef(self):
        return self.ctype + " " + self.name


class OMacro(OBase):
    def __init__(self, name, value):
        OBase.__init__(self, name, "", {PUBLIC})
        self.value = value

    def genC(self, f):
        if PUBLIC in self.mods:
            f.h << "#define " + self.name + " " + self.value
        else:
            f.c << "#define " + self.name + " " + self.value


class OMethod(OBase):
    def __init__(self, name, ctype, args=[], mods={PUBLIC}):
        OBase.__init__(self, name, ctype, mods)
        self.args = args
        self.code = []
        self.parent = None

    def arg(self):
        if len(self.args) == 0:
            return "(void)"
        alist = [ a.argDef() for a in self.args]
        return "("+ (", ".join(alist)) + ")"

    def genCS(self, f):
        if TEST in self.mods:
            f << "[TestMethod]"
        with f.block(self.csMods() + self.ctype + " " + self.name + " " + self.arg()):
            for code in self.code:
                f << code

    def genCPP(self, fh, fc):
        fh << self.csMods() + self.ctype + " " + self.name + self.arg() + ";"

        with fc.block(self.ctype + " " + self.parent.name + "::" + self.name + self.arg()):
            for code in self.code:
                fc << code

    def genC(self, f):
        funcname = self.parent.name + "_" + self.name

        f.c << ""
        with f.c.block(self.ctype + " " + funcname + " " + self.arg()):
            if REMEMBER in self.mods:
                f.c << "//{BEGIN:"+funcname+"}"
            for code in self.code:
                if isinstance(code, OBase):
                    code.genC(f)
                else:
                    f.c << code
            if REMEMBER in self.mods:
                f.c << "//{END:"+funcname+"}"
        
        if PUBLIC in self.mods:
            f.h << "extern " + self.ctype + " " + funcname + " " + self.arg() + ";"

    def __lshift__(self, s):
        self.code.append(s)
        return self


class OClass(OBase):
    def __init__(self, name, mods={PUBLIC}):
        OBase.__init__(self, name, name, mods)
        self.members = []

    def __lshift__(self, m):
        m.parent = self
        self.members.append(m)
        return self

    def genCS(self, f):
        if TEST in self.mods:
            f << "[TestClass]"
        with f.block(self.csMods() + "class " + self.name):
            for m in self.members:
                m.genCS(f)

    def genCPP(self, fh, fc):
        with fh.block(self.csMods() + "class " + self.name):
            for m in self.members:
                m.genCPP(fh, fc)
            fh << ";"

    def genC(self, f):
        for m in self.members:
            m.genC(f)

    def genPY(self, f):
        pass


class OStruct(OBase):
    def __init__(self, name, mods={PUBLIC}):
        OBase.__init__(self, name, name, mods)
        self.members = []

    def __lshift__(self, m):
        m.parent = self
        self.members.append(m)
        return self

    def genC(self, f):
        with f.h.block("typedef struct"):
            for m in self.members:
                m.genC(f)
        f.h << self.name + "_t;"


class OSwitch(OBase):
    def __init__(self, name, mods={PUBLIC}):
        OBase.__init__(self, name, "", mods)
        self.members = []

    def add(self, cond, code):
        self.members.append([cond,code])
        return self

    def genC(self, f):
        print(f)
        with f.c.block("switch (" + self.name + ")"):
            for cond, code in self.members:
                f.c << "case " + cond + ":"
                for line in code:
                    f.c << line
                f.c << "break;"

        
class OTestClass(OClass):
    def __init__(self, name):
        OClass.__init__(self, name, mods={PUBLIC,TEST})

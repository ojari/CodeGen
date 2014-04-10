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


class OFile(object):
    def __init__(self, fname):
        self.f = open(fname, "wt")
        self.indent = 0

    def __lshift__(self, s):
        if s == "}":
            self.indent -= 1
        #print ("\t"*self.indent) + self.line
        self.f.write(("\t"*self.indent) + s + "\n")
        if s == "{":
            self.indent += 1

    def addCsIncludes(self, includes):
        for inc in includes:
            self.f.write("using "+inc+";\n")
        self.f.write("\n")

    def close(self):
        self.f.close()
    
class OCFile(object):
    def __init__(self, fbase, fpath=""):
        self.c = OFile(fpath+fbase+".c")
        self.h = OFile(fpath+fbase+".h")

        self.h << "#ifndef _"+fbase.upper()+"_H"
        self.h << "#define _"+fbase.upper()+"_H"
        self.h << ""

        self.c << "#include \""+fbase+".hpp\""

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
        visible = {PRIVATE,PROTECTED,PUBLIC,STATIC}
        
        return " ".join( visible.intersection(self.mods) ) + " "


class OArg(OBase):
    def __init__(self, name, ctype, mods={PRIVATE}):
        OBase.__init__(self, name, ctype, mods)

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
        alist = [ a.argDef() for a in self.args]
        return "("+ (", ".join(alist)) + ")"

    def genCS(self, f):
        if TEST in self.mods:
            f << "[TestMethod]"
        f << self.csMods() + self.ctype + " " + self.name + " " + self.arg()
        f << "{"
        for code in self.code:
            f << code
        f << "}"

    def genC(self, f):
        funcname = self.parent.name + "_" + self.name

        f.c << ""
        f.c << self.ctype + " " + funcname + " " + self.arg()
        f.c << "{"
        for code in self.code:
            f.c << code
        f.c << "}"
        
        if PUBLIC in self.mods:
            f.h << "extern " + self.ctype + " " + funcname + " " + self.arg()

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
        f << self.csMods() + "class " + self.name
        f << "{"
        for m in self.members:
            m.genCS(f)
        f << "}"

    def genC(self, f):
        for m in self.members:
            m.genC(f)

    def genPY(self, f):
        pass
        
class OTestClass(OClass):
    def __init__(self, name):
        OClass.__init__(self, name, mods={PUBLIC,TEST})

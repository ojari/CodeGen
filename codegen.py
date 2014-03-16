
class OFile(object):
    def __init__(self, fname):
        self.f = open(fname, "wt")
        self.indent = 0

    def close(self):
        self.f.close()
    
class OCFile(object):
    def __init__(self, fbase):
        self.fc = OFile(fbase+".cpp")
        self.fh = OFile(fbase+".hpp")

        self.fh << "#ifndef _"+fbase.upper()+"_H"
        self.fh << "#define _"+fbase.upper()+"_H"
        self.fh << ""

        self.fc << "#include \""+fbase+".hpp\""
        self.fc << ""

    def close(self):
        self.fh << ""
        self.fh << "#endif"
        self.fh.close()
        self.fc.close()

class OBase(object):
    def __init__(self, name, ctype):
        self.name = name
        self.ctype = ctype
        self.mods = []

class OArgument(OBase):
    def __init__(self, name, ctype):
        OBase.__init__(name, ctype)

    def genCS(self, f):
        f << "public " + self.ctype + " " + self.name + ";"

class OMethod(OBase):
    def __init__(self, name, ctype, args=[]):
        OBase.__init__(name, ctype)
        self.args = args
        self.code = []

    def genCS(self, f):
        f << "public " + self.ctype + " " + self.name + " ()"
        f << "{"
        for code in self.code:
            m << code
        f << "}"

class OClass(OBase):
    def __init__(self, name):
        OBase.__init__(name, name)
        self.members = []

    def genCS(self, f):
        f << "public class " + self.name
        f << "{"
        for m in self.members:
            m.genCS(f)
        f << "}"

    def genC(self, f):
        pass

    def genPY(self, f):
        pass
        
class OTestClass(OClass):
    def __init__(self, name):
        OClass.__init__(name)

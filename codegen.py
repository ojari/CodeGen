#
# Copyright 2014-6 Jari Ojanen
#

# Possible values for OBase.mods list
#
PRIVATE   = "private"
PROTECTED = "protected"
PUBLIC    = "public"
STATIC    = "static"
FINAL     = "final"
TEST      = "test"
GETTER    = "getter"
SETTER    = "setter"
OVERRIDE  = "override"
DBVAR     = "db"
REMEMBER  = "remember"  # between code generations

# Possible values for LANGUAGE
#
LANG_C    = "C"
LANG_CPP  = "C++"
LANG_CS   = "C#"
LANG_JAVA = "JAVA"        # not supported yet
LANG_JS   = "JAVASCRIPT"  # not supported yet

from functools import wraps

CLASSES = []
INSTANCES = []
LANGUAGE = LANG_C


def q(s):
    return "\""+s+"\""


def p(l):
    a = ",".join(l)
    return "("+a+")"

def export(rtype):
    def func_wrap(func):
        func.export = 1
        func.rtype = rtype
        #print(func.__name__)
        #print(func)
        @wraps(func)
        def rfunc(*args, **kwargs):
            return func(*args, **kwargs)
        return rfunc
    return func_wrap

def exportclass(oclass):
    CLASSES.append(oclass)
    return oclass

def processExports():
    for c in CLASSES:
        o = c()
        m = [getattr(o,x) for x in dir(o) if "export" in dir(getattr(o,x))]

        for fn in m:
            meth = OMethod(fn.__name__, fn.rtype)
            fn(meth)
            o << meth
    
        INSTANCES.append(o)

# If class needs contructor parameters or some processing,
# this is replacement for processExports-getInstance system 
#
def handleExports(obj):
    m = [getattr(obj,x) for x in dir(obj) if "export" in dir(getattr(obj,x))]
    for fn in m:
        meth = OMethod(fn.__name__, fn.rtype)
        fn(meth)
        obj << meth


def getInstance(name):
    for i in INSTANCES:
        if i.name == name:
            return i
    return None

class OBlock(object):
    def __init__(self, parent):
        self.parent = parent

    def __enter__(self):
        self.parent << "{"

    def __exit__(self,a,b,c):
        self.parent << "}"

class OFile(object):
    def __init__(self, fname, namespace=""):
        print("generating "+fname+"...")
        self.fname = fname
        self.f = open(fname, "wt")
        self.indent = 0
        self.includes = []
        self.namespace = namespace

        global LANGUAGE
        if fname.endswith(".java"):
            LANGUAGE = LANG_JAVA
        elif fname.endswith(".cs"):
            LANGUAGE = LANG_CS
        elif fname.endswith(".js"):
            LANGUAGE = LANG_JAVASCRIPT

    def block(self, pre):
        self << pre
        return OBlock(self)

    def __lshift__(self, s):
        if s in ["}", "};"]:
            self.indent -= 1
        #print ("\t"*self.indent) + self.line
        self.f.write(("    "*self.indent) + s + "\n")
        if s == "{" or s.startswith("case "):
            self.indent += 1
        if s == "break;":
            self.indent -= 1
        return self

    def addIncludes(self):
        for inc in self.includes:
            if LANGUAGE == LANG_CS:
                self.f.write("using "+inc+";\n")
            elif LANGUAGE == LANG_JAVA:
                self.f.write("import "+inc+";\n")
            else:
                self.f.write("#include <"+inc+">\n")
        self.f.write("\n")

        if len(self.namespace) > 0 and LANGUAGE == LANG_CS:
            self << "namespace " + self.namespace
            self << "{"


    def close(self):
        if len(self.namespace) > 0:
            self << "}"
        self.f.close()


class OCFile(object):
    def __init__(self, fbase, fpath="", includes=[]):
        cExtra = ""
        hExtra = ""
        if "stm32" in fpath:
            cExtra = "src/"
            hExtra = "inc/"
        ext = ".c"
        if LANGUAGE == LANG_CPP:
            ext = ".cpp"
        self.c = OFile(fpath+cExtra+fbase+ext)
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
        self.doc = ""

    def got(self, item):
        return item in self.mods

    def isGetter(self):
        return GETTER in self.mods

    def isSetter(self):
        return SETTER in self.mods

    def isOverride(self):
        return OVERRIDE in self.mods

    def isDbVal(self):
        return DBVAR in self.mods
        
    def getMods(self):
        visible = {FINAL, PRIVATE, PROTECTED, PUBLIC, STATIC}
        if LANGUAGE == LANG_CPP:
            visible = {STATIC}
        
        return " ".join(visible.intersection(self.mods)) + " "


class OArg(OBase):
    def __init__(self, name, ctype, mods={PRIVATE}, initial=None):
        OBase.__init__(self, name, ctype, mods)
        self.initial = initial

    def genC(self, f):
        f.h << self.ctype + " " + self.name + ";"

    def genCPP(self, f):
        f.h << self.ctype + " " + self.name + ";"

    def genCS(self, f):
        post = ""
        if self.initial:
            post = " = " + self.initial
        f << self.getMods() + self.ctype + " " + self.name + post + ";"

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
        if len(self.args) == 0 and (LANGUAGE == LANG_C):
            return "(void)"
        alist = [ a.argDef() for a in self.args]
        return "("+ (", ".join(alist)) + ")"

    def genCS(self, f):
        f << ""
        if TEST in self.mods:
            f << "[TestMethod]"
        if self.isOverride():
            f << "@Override"
        with f.block(self.getMods() + self.ctype + " " + self.name + self.arg()):
            for code in self.code:
                f << code

    def genCPP(self, f):
        f.h << self.getMods() + self.ctype + " " + self.name + self.arg() + ";"

        with f.c.block(self.ctype + " " + self.parent.name + "::" + self.name + self.arg()):
            for code in self.code:
                f.c << code

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


class OEnum(OBase):
    def __init__(self, name, mods={PUBLIC}, items=[]):
        OBase.__init__(self, name, name, mods)
        self.items = items

    def add(self, item):
        self.items.append(item)

    def genCS(self, f):
        with f.block(self.getMods() + "enum " + self.name):
            for i in self.items:
                f << i + ","


def doBlock(f, name, items):
    with f.block(name):
        for i in items:
            f << i

class OProperty(OBase):
    def __init__(self, name, ctype, mods={PUBLIC}):
        OBase.__init__(self, name, ctype, mods)

        if self.name.startswith("_"):
            self.name = self.name[1:]
            self.name = self.name.capitalize()

        self.getter = []
        self.setter = []

    def genCS(self, f):
        with f.block(self.getMods() + self.ctype +" " + self.name):
            if self.isGetter():
                if len(self.getter) == 1:
                    f << "get { " + self.getter[0] + " }"
                else:
                    doBlock(f, "get", self.getter)
            if self.isSetter():
                if len(self.setter) == 1:
                    f << "set { " + self.setter[0] + " }"
                else:
                    doBlock(f, "set", self.setter)


class OClass(OBase):
    def __init__(self, name, mods={PUBLIC}):
        OBase.__init__(self, name, name, mods)
        self.members = []
        self.implements = []

    def __lshift__(self, m):
        m.parent = self
        self.members.append(m)
        return self

    def makeGetsSets(self):
        for i in self.members:
            if i.isGetter():
                m = OMethod("get_"+i.name, i.ctype, [])
                m << "return "+i.name+";"
                self << m
            if i.isSetter():
                m = OMethod("set_"+i.name, "void", [OArg("val", i.ctype)])
                m << i.name+" = val;"
                self << m

    def genCS(self, f):
        if len(self.doc) > 0:
            f << "/// <summary>"
            f << "/// " + self.doc
            f << "/// </summary>"
        if TEST in self.mods:
            f << "[TestClass]"

        post = ""
        if len(self.implements) > 0:
            if LANGUAGE == LANG_JAVA:
            	post = " implements "
            else:
                post = " : "
            post += ", ".join(self.implements)


        for i in self.members:
            if isinstance(i, OArg) and (i.isGetter() or i.isSetter()):
                p = OProperty(i.name, i.ctype)
                p.mods = i.mods
                p.mods.remove(PRIVATE)
                p.mods.add(PUBLIC)
                if i.isGetter():
                	p.getter = ["return "+i.name+";"]
                if i.isSetter():
                	p.setter = [i.name + " = value;"]
                self << p

        with f.block(self.getMods() + "class " + self.name + post):
            for m in self.members:
                m.genCS(f)

    def genCPP(self, f):
        self.makeGetsSets()
        with f.h.block(self.getMods() + "class " + self.name):
            for prot in [PUBLIC, PROTECTED, PRIVATE]:
                items = [x for x in self.members if x.got(prot)]
                f.h << prot + ":"
                for m in items:
                    m.genCPP(f)
        f.h << ";"

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


#-------------------------------------------------------------------------------
def write_file(c, path):
    f = OCFile(c.name, path, includes=["hw.h"])
    c.genC(f)
    f.close()

def write_file_cs(lst, fname: str, namespace: str, includes=[]):
    f = OFile(fname, namespace)
    f.includes = includes
    f.addIncludes()
    for c in lst:
    	c.genCS(f)
    f.close()

def write_file_cpp(c, path):
    global LANGUAGE

    LANGUAGE = LANG_CPP
    f = OCFile(c.name, path, includes=[])
    c.genCPP(f)
    f.close()


def write_file_n(fname, path, *classes):
    f = OCFile(fname, path, includes=["hw.h"])
    for c in classes:
        if isinstance(c, list):
            for ci in c:
                ci.genC(f)
        else:
            c.genC(f)
    f.close()

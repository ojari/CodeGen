#
# Copyright 2014-6 Jari Ojanen
#
from enum import Flag, auto
from functools import wraps
import os.path
import logging


class Mod(Flag):
    PRIVATE   = auto()
    PROTECTED = auto()
    PUBLIC    = auto()
    STATIC    = auto()
    CONST     = auto()
    FINAL     = auto()
    TEST      = auto()
    GETTER    = auto()
    SETTER    = auto()
    OVERRIDE  = auto()
    DBVAR     = auto()
    REMEMBER  = auto() # remember code between {BEGIN:func} ... {END:func}
    EXTERNAL  = auto()

CLASSES = []
INSTANCES = []
NEWLINE = "\n"

def q(s: str):
    return "\""+s+"\""

def c(*items):
    lst = []

    for i in items:
        if isinstance(i, str):
            lst.append(i)
        elif isinstance(i, OArg):
            lst.append(i.name)
        else:
            lst.append("????")

    return "(" + (", ".join(lst)) + ")"

def export(rtype):
    def func_wrap(func):
        func.export = 1
        func.rtype = rtype
        #logging.debug(func.__name__)
        #logging.debug(func)
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


def flatten(l):
    for el in l:
        if isinstance(el, list) and not isinstance(el, str):
            for sub in flatten(el):
                yield sub
        else:
            yield el

class OBlock(object):
    def __init__(self, parent, post=None):
        self.parent = parent
        self.post = post

    def __enter__(self):
        self.parent << "{"

    def __exit__(self,a,b,c):
        self.parent << "}"
        if self.post:
            self.parent << self.post

class OFile(object):
    def __init__(self, fname, generator, namespace=""):
        logging.info("generating "+fname+"...")
        self.fname = fname
        self.f = open(fname, "wt")
        self.indent = 0
        self.includes = []
        self.namespace = namespace

        self.generator = generator
        self.generator.open(os.path.basename(fname), self)

    def block(self, pre, post=None):
        if isinstance(pre, list):
            for i in pre:
                self << pre
        else:
            self << pre
        return OBlock(self, post)

    def __lshift__(self, s):
        if isinstance(s, OBase):
            s.accept(self.generator, self)
            return self

        if s in ["}", "};"]:
            self.indent -= 1
        #print ("\t"*self.indent) + self.line
        if s in ['public:', 'protected:', 'private:']:
            self.f.write(s + NEWLINE)
        else:
            self.f.write(("    "*self.indent) + s + NEWLINE)

        if s == "{" or s.startswith("case "):
            self.indent += 1
        if s == "break;":
            self.indent -= 1
        return self

    def addIncludes(self, visitor):
        for inc in self.includes:
            visitor.addInclude(inc, self)
        self << ""

        #if len(self.namespace) > 0 and isLang(LANG_CS):
        #    self << "namespace " + self.namespace
        #    self << "{"


    def close(self):
        if len(self.namespace) > 0:
            self << "}"
        self.generator.close(self)
        self.f.close()


class OBase(object):
    def __init__(self, name: str, ctype: str, mods):
        self.name = name
        self.ctype = ctype
        self.mods = mods
        self.doc = ""
        self.pre = []

    def got(self, item: Mod):
        return item in self.mods

    def isGetter(self):
        return Mod.GETTER in self.mods

    def isSetter(self):
        return Mod.SETTER in self.mods

    def isOverride(self):
        return Mod.OVERRIDE in self.mods

    def isDbVal(self):
        return Mod.DBVAR in self.mods
        
    def getMods(self, visible=[Mod.FINAL, Mod.PRIVATE, Mod.PROTECTED, Mod.PUBLIC, Mod.STATIC, Mod.CONST, Mod.OVERRIDE]):
        ###if isLang(LANG_CPP):
        ###    visible = {Mod.STATIC}
        
        mods = []
        for v in visible:
            if v in self.mods:
                mods.append(v.name.lower())

        #return " ".join(visible.intersection(self.mods)) + " "
        return " ".join(mods) + " "

    def accept(self, visitor, f):
        visitor.visit(self, f)

    def define(self):
        if self.parent and self.parent.name == self.name:  # constructor
            return self.name
        return self.ctype + " " + self.name

class OArg(OBase):
    def __init__(self, name: str, ctype: str, mods=None, initial=None):
        if mods is None:     # fix all instances using a same mutable set.
            mods = {Mod.PRIVATE}
        OBase.__init__(self, name, ctype, mods)
        self.initial = initial
        self.parent = None

class OEmptyLine(OBase):
    def __init__(self):
        OBase.__init__(self, None, None, {Mod.PUBLIC})


class OMacro(OBase):
    def __init__(self, name, value):
        if isinstance(name, list):
            name = "_".join(name)
        OBase.__init__(self, name, "", {Mod.PUBLIC})
        self.value = value

class OMethod(OBase):
    def __init__(self, name: str, ctype: str, args=[], mods={Mod.PUBLIC}):
        OBase.__init__(self, name, ctype, mods)
        self.args = args
        self.base = ""
        self.code = []
        self.parent = None

    def setCode(self, code):
        self.code = [line.strip() for line in code.strip().split("\n")]

    def arg(self):
        alist = [ a.define() for a in self.args]
        return "("+ (", ".join(alist)) + ")"

    def getCppDefine(self, visible=None):
        return self.getMods(visible) + self.define() + self.arg()

    def getCFuncName(self) -> str:
        funcname = self.name
        if self.parent is not None:
            funcname = self.parent.name + "_" + self.name
        return funcname

    def __lshift__(self, s):
        if isinstance(s, str):
	        self.code.append(s)
        elif isinstance(s, OBase):
            self.code.append(s)
        else:
            for line in flatten(s):
                self.code.append(line)
        return self


class OEnum(OBase):
    def __init__(self, name: str, mods={Mod.PUBLIC}, items=[]):
        OBase.__init__(self, name, name, mods)
        self.items = list(items) # make copy of list

    def add(self, item: str):
        self.items.append(item)

def doBlock(f, name, items):
    with f.block(name):
        for i in items:
            f << i

class OProperty(OBase):
    def __init__(self, name: str, ctype, mods={Mod.PUBLIC}):
        OBase.__init__(self, name, ctype, mods)

        if self.name.startswith("_"):
            self.name = self.name[1].upper() + self.name[2:]

        self.getter = []
        self.setter = []


class OClass(OBase):
    def __init__(self, name: str, mods={Mod.PUBLIC}):
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


class OStruct(OBase):
    def __init__(self, name: str, mods={Mod.PUBLIC}):
        OBase.__init__(self, name, name, mods)
        self.members = []

    def __lshift__(self, m):
        m.parent = self
        self.members.append(m)
        return self


class OSwitch(OBase):
    def __init__(self, name: str, mods={Mod.PUBLIC}):
        OBase.__init__(self, name, "", mods)
        self.members = []

    def add(self, cond, code):
        self.members.append([cond,code])
        return self

        
class OTestClass(OClass):
    def __init__(self, name: str):
        OClass.__init__(self, name, mods={Mod.PUBLIC, Mod.TEST})


#-------------------------------------------------------------------------------
def write_file(c, filename: str, generator, includes=[]):
    f = OFile(filename, generator)
    f.includes = includes
    f.addIncludes(generator) 
    if isinstance(c, list):
        for ci in c:
            f << ci
    else:
        f << c
    f.close()

def write_file_n(data, *classes):
    for fname, gen in data:
        f = OFile(fname, gen)
        if fname.endswith('.c'):
            fbase = os.path.basename(fname)
            f.includes = ['hw.h', fbase+".h"]
            f.addIncludes(gen)
        for c in classes:
            if isinstance(c, list):
                for ci in c:
                    f << ci
            else:
                f << c
        f.close()

#
# for generating code inside method
#
def block(name, items):
    return [name, '{'] + items + ['}']

def IF(cond, items):
    return block("if (" + cond + ")", items)

def ELSE(items):
    return block("else", items)

def ELSEIF(cond, items):
    return block("else if (" + cond + ")", items)

def FOREACH(cond, items):
    return block("foreach (" + cond + ")", items)

def SWITCH(cond, items):
    return block("switch(" + cond + ")", items)

def CASE(cond, items):
    return ["case "+ cond + ":"] + items + ["break;"]

def NEW(ctype, variable, args):
    return ctype + " " + variable + " = new " + ctype + "(" + args + ")"

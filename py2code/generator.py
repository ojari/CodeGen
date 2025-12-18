from .codegen import Mod, q, OBase, OClass, OArg, OMethod
#
# Visitor pattern for code generation
#
class CodeGenerator:
    """
    The Visitor base class for generating code.
    Each concrete generator for a language (C, C#, etc.) will inherit from this.
    """
    def visit(self, node, f):
        method_name = 'visit_' + node.__class__.__name__.lower()
        visitor = getattr(self, method_name, None)
        if visitor is None and isinstance(node, OClass):
            visitor = getattr(self, 'visit_oclass', self.generic_visit)
        if visitor is None and isinstance(node, OArg):
            visitor = getattr(self, 'visit_oarg', self.generic_visit)
        if visitor is None and isinstance(node, OMethod):
            visitor = getattr(self, 'visit_omethod', self.generic_visit)

        if visitor is None:
            return self.generic_visit(node, f)
        
        return visitor(node, f)

    def generic_visit(self, node, f):
        # Default behavior: do nothing or raise an error
        # For container-like nodes, you might want to visit children
        pass

    def visit_oswitch(self, node, f):
        with f.block("switch (" + node.name + ")"):
            for cond, code in node.members:
                f << "case " + cond + ":"
                for line in code:
                    f << line
                f << "break;"

    def addInclude(self, inc, f):
        if inc.startswith("<"):
            f << "#include " + inc
        else:
            f << "#include " + q(inc)

    def open(self, fname, f):
        pass

    def close(self, f):
        pass

    def write_cmeth(self, node, f, funcname):
        if node.doc:
            f << "/** " + node.doc
            f << " */"
        with f.block(node.ctype + " " + funcname + node.arg()):
            if node.got(Mod.REMEMBER):
                f << "//{BEGIN:" + funcname + "}"
            for code in node.code:
                if isinstance(code, OBase):
                    self.visit(code, f)
                else:
                    f << code
            if node.got(Mod.REMEMBER):
                f << "//{END:" + funcname + "}"

class HeaderGenerator(CodeGenerator):
    def addInclude(self, inc, f):
        if inc.startswith("<"):
            f << "#include " + inc
        else:
            f << "#include " + q(inc)

    def open(self, fname, f):
        guard = fname.upper().replace(".", "_").replace("/", "_").replace("\\", "_")
        f << "#ifndef " + guard
        f << "#define " + guard
        f << ""

    def close(self, f):
        f <<  ""
        f << "#endif"

class CSGenerator(CodeGenerator):
    def addInclude(self, inc, f):
        f << "using " + inc + ";"
    
    def visit_oarg(self, node, f):
        post = ""
        if node.initial:
            post = " = " + node.initial
        if len(node.pre) > 0:
            for line in node.pre:
                f << line
        f << node.getMods() + node.define() + post + ";"

    def visit_omethod(self, node, f):
        if node.got(Mod.TEST):
            f << "[TestMethod]"
        # In a real Java generator, this would be handled there.
        # if isLang(LANG_JAVA) and node.isOverride():
        #     f << "@Override"
        base = node.base
        if len(base) > 0:
            base = f" : base({base})"
        with f.block(node.getCppDefine() + base):
            for code in node.code:
                if isinstance(code, OBase):
                    self.visit(code, f)
                else:
                    f << code

    def visit_oenum(self, node, f):
        with f.block(node.getMods() + "enum " + node.name):
            for i in node.items:
                f << i + ","

    def visit_oproperty(self, node, f):
        if len(node.pre) > 0:
            for line in node.pre:
                f << line
        with f.block(node.getMods() + node.define()):
            if node.isGetter():
                if len(node.getter) == 1:
                    f << "get { " + node.getter[0] + " }"
                else:
                    doBlock(f, "get", node.getter)
            if node.isSetter():
                if len(node.setter) == 1:
                    f << "set { " + node.setter[0] + " }"
                else:
                    doBlock(f, "set", node.setter)

    def visit_oclass(self, node, f):
        if len(node.doc) > 0:
            f << "/// <summary>"
            f << "/// " + node.doc
            f << "/// </summary>"
        if node.got(Mod.TEST):
            f << "[TestClass]"

        post = ""
        if len(node.implements) > 0:
            post = " : "
            post += ", ".join(node.implements)

        getsets = []
        for i in node.members:
            if isinstance(i, OArg) and (i.isGetter() or i.isSetter()):
                p = OProperty(i.name, i.ctype)
                p.mods = {Mod.PUBLIC} | (i.mods & {Mod.GETTER, Mod.SETTER})
                if i.isGetter():
                    p.getter = ["return " + i.name + ";"]
                if i.isSetter():
                    p.setter = [i.name + " = value;"]
                getsets.append(p)
        node.members.extend(getsets)

        with f.block(node.getMods() + "class " + node.name + post):
            first = True
            for m in node.members:
                if not first and not isinstance(m, OArg):
                    f << ""
                first = False
                self.visit(m, f)

    def visit_oswitch(self, node, f):
        with f.block("switch (" + node.name + ")"):
            for cond, code in node.members:
                f << "case " + cond + ":"
                for line in code:
                    f << line
                f << "break;"

class CGenerator(CodeGenerator):
    def visit_oarg(self, node, f):
        if node.doc:
            f << "/** " + node.doc
            f << " */"
        pre = ""
        if node.got(Mod.EXTERNAL):
            pre = "extern "
        if node.initial is None:
            f << pre + node.define() + ";"
        elif isinstance(node.initial, str):
            f << pre + node.define() + ";"
        elif isinstance(node.initial, list):
            f << pre + node.define() + " = {"
            for item in node.initial:
                f << item
            f << "};"

    def visit_oemptyline(self, node, f):
        if not node.got(Mod.PUBLIC):
            f << ""

    def visit_omacro(self, node, f):
        if not node.got(Mod.PUBLIC):
            f << "#define " + node.name + " " + node.value

    def visit_omethod(self, node, f):
        if node.got(Mod.EXTERNAL):
            return

        f << ""
        self.write_cmeth(node, f, node.getCFuncName())

    def visit_oclass(self, node, f):
        for m in node.members:
            self.visit(m, f)

    def visit_ostruct(self, node, f):
        pass  # Struct definition is in the header

    def visit_oswitch(self, node, f):
        with f.block("switch (" + node.name + ")"):
            for cond, code in node.members:
                f << "case " + cond + ":"
                for line in code:
                    f << line
                f << "break;"

    def visit_ostruct(self, node, f):
        if node.got(Mod.PRIVATE):
            node.gen(f)

class HGenerator(HeaderGenerator):
    def visit_oarg(self, node, f):
        pre = ""
        if node.got(Mod.EXTERNAL):
            pre = "extern "
        f << pre + node.define() + ";"

    def visit_oswitch(self, node, f):
        pass

    def visit_oemptyline(self, node, f):
        if node.got(Mod.PUBLIC):
            f << ""

    def visit_omacro(self, node, f):
        if node.got(Mod.PUBLIC):
            f << "#define " + node.name + " " + node.value

    def visit_omethod(self, node, f):
        if node.got(Mod.PUBLIC):
            f << "extern " + node.ctype + " " + node.getCFuncName() + " " + node.arg() + ";"

    def visit_oenum(self, node, f):
        with f.block("typedef enum ", node.name + ";"):
            for i in node.items:
                f << i + ","

    def visit_oclass(self, node, f):
        methods = [m for m in node.members if isinstance(m, OMethod)]
        attrs = [m for m in node.members if isinstance(m, OArg)]
        if len(attrs) > 0:
            with f.block("typedef struct " + node.name):
                for a in attrs:
                    self.visit(a, f)
            f << node.name + "_t;"

        for m in methods:
            self.visit(m, f)

    def visit_ostruct(self, node, f):
        if node.got(Mod.PUBLIC):
            with f.block("struct " + node.name):
                for a in node.members:
                    self.visit(a, f)
            f << ";"

class CPPGenerator(CodeGenerator):
    def visit_oarg(self, node, f):
        pass  # Member variables are handled in the header

    def visit_omethod(self, node, f):
        self.write_cmeth(node, f, node.parent.name + "::" + node.name)

    def visit_oclass(self, node, f):
        for prot in [Mod.PUBLIC, Mod.PROTECTED, Mod.PRIVATE]:
            items = [x for x in node.members if x.got(prot)]
            for m in items:
                self.visit(m, f)

    def visit_oswitch(self, node, f):
        with f.block("switch (" + node.name + ")"):
            for cond, code in node.members:
                f << "case " + cond + ":"
                for line in code:
                    f << line
                f << "break;"

class HPPGenerator(HeaderGenerator):
    def visit_omethod(self, node, f):
        f << node.getCppDefine([Mod.FINAL, Mod.STATIC, Mod.CONST, Mod.OVERRIDE]) + ";"

    def visit_oarg(self, node, f):
        f << node.define() + ";"

    def visit_oclass(self, node, f):
        node.makeGetsSets()
        with f.block(node.getMods([Mod.STATIC]) + "class " + node.name):
            for prot in [Mod.PUBLIC, Mod.PROTECTED, Mod.PRIVATE]:
                items = [x for x in node.members if x.got(prot)]
                f << prot.name.lower() + ":"
                for m in items:
                    self.visit(m, f)
        f << ";"

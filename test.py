from enum import Flag, auto


class FileType(Flag):
    C    = (".c",    "GenC")
    H    = (".h",    "GenH")
    CPP  = (".cpp",  "GenCPP")
    HPP  = (".hpp",  "GetHPP")
    CS   = (".cs",   "GenCS")
    JAVA = (".java", "GenCS")
    JS   = (".js",   "GenCS")

    def __init__(self, extension, function):
        self.extension = extension
        self.function = function

class Mods(Flag):
    PRIVATE   = "private"
    PROTECTED = "protected"
    PUBLIC    = "public"
    STATIC    = "static"
    CONST     = "const"
    FINAL     = "final"
    TEST      = "test"
    GETTER    = "getter"
    SETTER    = "setter"
    OVERRIDE  = "override"
    DBVAR     = "db"
    REMEMBER  = "remember"  # between code generations
    EXTERNAL  = "external"

aa = FileType.C | FileType.H

bb = FileType.C in aa

cc = FileType.H in aa


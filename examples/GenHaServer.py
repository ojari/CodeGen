#from gen import JDbAttr
from py2code.codegen import OClass, q, OArg, write_file, Mod
from py2code.codegen import exportclass, export, getInstance, processExports, handleExports
from py2code.generator import CPPGenerator, HPPGenerator

FLDS_SERVER = [["Time",  "INTEGER PRIMARY KEY"],
               ["Temp1", "REAL"],
               ["Temp2", "REAL"],
               ["Temp3", "REAL"],
               ["Temp4", "REAL"],
               ["Hum1",  "REAL"]
              ]

FLDS_WEATHER = [["Time", "INTEGER PRIMARY KEY"],
                ["Temp", "REAL"],
                ["DP",   "REAL"],
                ["Wind", "REAL"]
               ]

FLDS_STOCK = [["Time", "INTEGER PRIMARY KEY"],
              ["Company", "TEXT"],
              ["Value",   "REAL"]
             ]

FLDS_VDR = [["Channel", "TEXT"],
            ["Start",   "INTEGER"],
            ["Stop",    "INTEGER"],
            ["Name",    "TEXT"],
            ["Desc",    "TEXT"]
           ]


class JDbAttr(OArg):
    def __init__(self, name, dbtpe):
        ctype = "int"
        if dbtpe == "REAL":
            ctype = "double"
        elif dbtpe == "TEXT":
            ctype = "std::string"
        else:
            ctype = "int"
        OArg.__init__(self, name, ctype)
        self.dbtpe = dbtpe

VOID = "void"
CCHAR = "const char*"
STR = "std::string&"

class Measure(OClass):
    def __init__(self, name, fields):
        OClass.__init__(self, name, {Mod.PUBLIC})
        self.implements = ["Query"]

        self.dbargs = []
        for fld, dtype in fields:
            dbArg = JDbAttr(fld, dtype)
            self << dbArg
            self.dbargs.append(dbArg)

        s = ", ".join([a.name+" "+a.ctype for a in self.dbargs])
        self.CREATE = "CREATE TABLE "+self.name+" ("+s+")"
        self.INSERT = "INSERT INTO " + self.name + " VALUES("
        self.SELECT = "SELECT * FROM " + self.name + ";"

    @export(CCHAR)
    def SqlCreate(self, meth):
        meth << "return " + q(self.CREATE) + ";"

    @export(STR)
    def SqlInsert(self, meth):
        meth << "std::ostringstream os;"
        meth << "os << " + q(self.INSERT) + ";"
        for v in self.dbargs:
            meth << "os << " + v.name + " << \",\""
        meth << "os << \")\";"
        meth << "return os.str();"

    @export(VOID)
    def SqlGet(self, meth):
        meth << "std::string query = " + q(self.SELECT) + ";"

    @export(VOID)
    def HandleRow(self, meth):
        index = 0
        for v in self.dbargs:
            if v.dbtpe == "REAL":
                fn = "sqlite3_column_double"
            else:
                fn = "sqlite3_column_int"
            meth << v.name + " = "+fn+"(_statement, "+str(index)+");"
            index += 1

    @export(STR)
    def JsonGet(self, meth):
        meth << "rapidjson::Document doc;"
        meth << "doc.SetObject();"
        for v in self.dbargs:
            meth << "doc.AddMember(" + q(v.name) + ", " + v.name + ", doc.GetAllocator());"
        meth << ""
        meth << "rapidjson::StringBuffer strbuf;"
        meth << "rapidjson::Writer<rapidjson::StringBuffer> writer(strbuf);"
        meth << "doc.Accept(writer);"
        meth << ""
        meth << "return strbuf.GetString();"

    @export(VOID)
    def JsonSet(self, meth):
        meth.args = [OArg("json", "const char*")]

        meth << "rapidjson::Document doc;"
        meth << "doc.Parse(json);"
        for v in self.dbargs:
            meth << v.name + " = doc[" + q(v.name) + "];"

#-----------------------------------------------------------------------
ct = Measure("TblMeasure", FLDS_SERVER)
handleExports(ct)
write_file(ct, "out/db_meas.cpp",  CPPGenerator(), ["db_meas.h"])
write_file(ct, "out/db_meas.h",    HPPGenerator())


cs = Measure("TblWeather", FLDS_WEATHER)
handleExports(cs)
write_file(cs, "out/db_weather.cpp",  CPPGenerator(), ["db_weather.h"])
write_file(cs, "out/db_weather.h",    HPPGenerator())


cs = Measure("TblStock", FLDS_STOCK)
handleExports(cs)
write_file(cs, "out/db_stock.cpp",  CPPGenerator(), ["db_stock.h"])
write_file(cs, "out/db_stock.h",    HPPGenerator())


cs = Measure("TblVdr", FLDS_VDR)
handleExports(cs)
write_file(cs, "out/db_vdr.cpp",  CPPGenerator(), ["db_vdr.h"])
write_file(cs, "out/db_vdr.h",    HPPGenerator())

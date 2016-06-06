from gen import JDbAttr
from codegen import OClass, q, OArg, write_file_cpp, PUBLIC, STATIC
from codegen import exportclass, export, getInstance, processExports, handleExports

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

VOID = "void"
CCHAR = "const char*"
STR = "std::string&"

class Measure(OClass):
    def __init__(self, name, fields):
        OClass.__init__(self, name, {PUBLIC})
        self.implements = ["Query"]

        self.dbargs = []
        for fld, dtype in fields:
            dbArg = JDbAttr(fld, dtype)
            self << dbArg
            self.dbargs.append(dbArg)

        s = ", ".join([a.name+" "+a.dbtpe for a in self.dbargs])
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
write_file_cpp(ct, "tmp/")


cs = Measure("TblWeather", FLDS_WEATHER)
handleExports(cs)
write_file_cpp(cs, "tmp/")


cs = Measure("TblStock", FLDS_STOCK)
handleExports(cs)
write_file_cpp(cs, "tmp/")


cs = Measure("TblVdr", FLDS_VDR)
handleExports(cs)
write_file_cpp(cs, "tmp/")

#
# Copyright 2014 Jari Ojanen
#
# A very simple parser for emacs org-mode tables.
#
class ParseOrg:
    def __init__(self, fname):
        self.f = open(fname, "rt")


    def parse(self):
        line = self.f.readline()
        while line[0] != "|":
            line = self.f.readline()

        ret = []
        while line[0] == "|":
            if not line.startswith("|-"):
                line = line.strip()
                arr = line[1:-1].split("|")
                ret.append( [ i.strip() for i in arr] )
            line = self.f.readline()

        return ret

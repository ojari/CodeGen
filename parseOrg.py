#
# Copyright 2014 Jari Ojanen
#
# A very simple parser for emacs org-mode tables.
#
import logging

class OrgHeader:
    def __init__(self, level, name):
        self.level = level
        self.name = name
        self.items = []

    def add(self, child):
        self.items.append(child)

    def __repr__(self):
        return "<H{1} {0} childs={2}>".format(self.name, self.level, len(self.items))

class OrgTable:
    def __init__(self):
        self.items = []


class ParseOrg:
    def __init__(self, fname):
        self.f = open(fname, "rt")
        self.items = []
        self.vars = {}

    def parseTable(self, line):
        ret = []
        while line[0] == "|":
            if not line.startswith("|-"):
                line = line.strip()
                arr = line[1:-1].split("|")
                ret.append( [ i.strip() for i in arr] )
            line = self.f.readline()

        return ret

    def parseHeader(self, line):
        pos = line.find(" ")
        if pos > 0:
            return OrgHeader(pos, line[pos:])
        return line
    
    def parse(self):
        line = self.f.readline()
        curHeader = None
        while len(line) != 0:
            line = line.strip()
            if len(line) == 0:
                pass
            elif line[0] == "|":
                curHeader.add( self.parseTable(line) )
            elif line[0] == "*":
                curHeader = self.parseHeader(line)
                self.items.append( curHeader )
            elif line[0:2] == "#+":
                name, value = line[2:].split(":")
                self.vars[name] = value.strip()
            else:
                logging.debug("Invalid org item:" + line)

            line = self.f.readline()

#p = ParseOrg("/home/ABB/CodesysComm/doc/protocol.org")
#p.parse()

#print(p.items)

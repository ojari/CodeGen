import sys

#print(sys.argv[1])

FNAME = sys.argv[1]
MODULE = FNAME[:-4].upper()

print("generating "+MODULE+"...")
#exit(0)


#MODULE="RFM12"

def define(name, value):
    print "#define "+"_".join(name)+" "+value

def sbits(value, offset):
    ret = []
    for i in range(0,7):
        bit = 2**i
        if (bit & value):
            ret.append("BIT"+str(i+offset))
    return " | ".join(ret)

def convValue(s):
    s = s.replace("-", "m")
    return s

class Register:
    def __init__(self, name, addr):
        self.name = name
        self.addr = addr
        self.data = []

    def dump(self):
        define( [MODULE,self.name], self.addr)
        cbit = 0
        for reg,bits,arg in self.data:
            if bits == 1:
                define([MODULE,self.name,reg.upper()], "BIT"+str(cbit))
            elif bits in [2,3,4]:
                if len(arg) == 0: # use numbers
                    for v in range(0,2**bits):
                        define([MODULE,self.name,reg.upper(),str(v)], sbits(v, cbit))
                else: # use names
                    items = arg.split(",")
                    for v in range(0,2**bits):
                        if v < len(items) and items[v] != "-":
                            define([MODULE,self.name,reg.upper(),convValue(items[v])], sbits(v, cbit))
            else:
                print "   ",reg,bits,cbit,2**bits
            cbit += bits

f = open(FNAME)
r = None
for line in f.readlines():
    if line.startswith("* "):
        pos = line.find("#")  # remove comment
        if pos > 0:
            line = line[:pos].strip()
        name,addr = line[2:].split(" ")
        if r != None:
            r.dump()
        if "-" in addr:  # is range
            r = None
            adr1,adr2 = addr.split("-")
            adr1 = int(adr1, 16)
            adr2 = int(adr2, 16)
            for i,a in enumerate(range(adr1,adr2+1)):
                define([MODULE,name,str(i+1)], hex(a))
        else:            # is single value
            r = Register(name, addr.strip())
        
    elif line.startswith(" - "):
        bs = line[3:].strip()
        arg = ""
        cmt = bs.find("/")
        if cmt > 0:
            bs = bs[:cmt].strip()
        if bs in ["0","1"]:
            continue
        if " " in bs:
            bs,arg = bs.split(" ")
        #print "B"+bs+"."
        reg,bits = bs.split(":")
        r.data.append([reg,int(bits),arg])
        
    elif len(line.strip()) == 0:
        pass
    
    else:
        print " <"+line+">"

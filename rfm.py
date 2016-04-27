from codegen import OClass, OMacro, write_file

MODULE = "rfm12b"
PATH = "../Drivers/"

cc = OClass(MODULE)

def HandleCommand(f, header):xf
    cmd,addr = header.split(" ")

    cc << OMacro("_".join([MODULE.upper(), "CMD", cmd]),  
                 addr)

    bit = 0
    while 1:
        line = f.readline().strip()
        if not line.startswith("-"):
            break
        
        line = line[2:]
        if " " in line:
            line = line[:line.find(" ")]
        if line in ["0", "1"]:
            bit += 1
            continue

        bname, blen = line.split(":")
        
        if blen=="1":
            cc << OMacro("_".join([MODULE.upper(), cmd ,bname.upper()]), 
                         "BIT_"+str(bit))
        else:
            print("\t" + str(bit)+ " - " + bname + "." + blen + ".")
        bit += int(blen)
    #for bno, desc in zip(bits,desc):
    #    if desc in ['0', '1']:
    #        continue
    #    print("\tRFM12B_" + cmd + "_" + desc + "  BIT"+ bno)


f = open("rfm12b.org")
while 1:
    line = f.readline()
    if len(line) == 0:
        break
    if line.startswith("*"):
        f.readline()
        HandleCommand(f, line[2:].strip())


write_file(cc, PATH)

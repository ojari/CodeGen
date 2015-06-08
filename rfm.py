MODULE = "RF12B"

def define(lst, value):
    print("#define " + ("_".join(lst)) + " " + str(value))

def HandleCommand(f, header):
    cmd,addr = header.split(" ")

    define([MODULE, "CMD", cmd], addr)

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
            define([MODULE, cmd, bname.upper()], "BIT_"+str(bit))
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

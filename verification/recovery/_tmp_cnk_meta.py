import struct
# SYSTEM.CNF
p=r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc'
import os
for f in os.listdir(p):
    print(f)
cnf=None
for name in os.listdir(p):
    if name.upper()=='SYSTEM.CNF':
        cnf=os.path.join(p,name)
if cnf:
    print('SYSTEM.CNF:', open(cnf,'rb').read())
# identity
print(open(r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\identity.json').read())
# comment section
elf=open(r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf','rb').read()
print('comment:', elf[0x5F20AD:0x5F20AD+0x2B])

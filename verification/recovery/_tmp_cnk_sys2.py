import struct, collections

elf_path = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data = open(elf_path,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80
text = data[FILE_OFF:FILE_OFF+0x5F2000]

stubs = collections.Counter()
stub_va = {}
for i in range(0, len(text)-8, 4):
    w0 = struct.unpack_from('<I', text, i)[0]
    w1 = struct.unpack_from('<I', text, i+4)[0]
    if (w1 & 0xFC00003F) != 0x0000000C:
        continue
    imm = None
    if (w0 & 0xFFFF0000) == 0x24030000:
        imm = w0 & 0xFFFF
        if imm >= 0x8000: imm -= 0x10000
    elif (w0 & 0xFFFF0000) == 0x34030000:
        imm = w0 & 0xFFFF
    if imm is None:
        continue
    stubs[imm] += 1
    stub_va.setdefault(imm, []).append(LOAD_VA+i)

HLE = {
0x01:'ResetEE',0x02:'GsSetCrt',0x04:'Exit',0x05:'_ExceptionEpilogue',0x06:'LoadExecPS2',0x07:'ExecPS2',
0x10:'AddIntcHandler',0x11:'RemoveIntcHandler',0x12:'AddDmacHandler',0x13:'RemoveDmacHandler',
0x14:'EnableIntc',0x15:'DisableIntc',0x16:'EnableDmac',0x17:'DisableDmac',
0x18:'SetAlarm',0x19:'ReleaseAlarm',0x1A:'iEnableIntc',0x1B:'iDisableIntc',0x1C:'iEnableDmac',0x1D:'iDisableDmac',
0x1E:'iSetAlarm',0x1F:'iReleaseAlarm',
0x20:'CreateThread',0x21:'DeleteThread',0x22:'StartThread',0x23:'ExitThread',0x24:'ExitDeleteThread',
0x25:'TerminateThread',0x26:'iTerminateThread',
0x29:'ChangeThreadPriority',0x2A:'iChangeThreadPriority',0x2B:'RotateThreadReadyQueue',0x2C:'iRotateThreadReadyQueue',
0x2D:'ReleaseWaitThread',0x2E:'iReleaseWaitThread',0x2F:'GetThreadId',0x30:'ReferThreadStatus',0x31:'iReferThreadStatus',
0x32:'SleepThread',0x33:'WakeupThread',0x34:'iWakeupThread',0x35:'CancelWakeupThread',0x36:'iCancelWakeupThread',
0x37:'SuspendThread',0x38:'iSuspendThread',0x39:'ResumeThread',0x3A:'iResumeThread',
0x3C:'SetupThread',0x3D:'SetupHeap',0x3E:'EndOfHeap',
0x40:'CreateSema',0x41:'DeleteSema',0x42:'SignalSema',0x43:'iSignalSema',0x44:'WaitSema',
0x45:'PollSema',0x46:'iPollSema',0x47:'ReferSemaStatus',0x48:'iReferSemaStatus',
0x4A:'SetOsdConfigParam',0x4B:'GetOsdConfigParam',0x5B:'GetEntryAddress',
0x64:'FlushCache',0x68:'iFlushCache',0x6B:'SifStopDma',
0x70:'GsGetIMR',0x71:'GsPutIMR',0x73:'SetVSyncFlag',0x74:'SetSyscall',
0x76:'SifDmaStat',0x77:'SifSetDma',0x78:'SifSetDChain',0x79:'SifSetReg',0x7A:'SifGetReg',
0x7C:'Deci2Call',0x7E:'MachineType',0x7F:'GetMemorySize',
}

print('li v1; syscall stub pairs:', sum(stubs.values()))
unhandled=[]
for imm,c in stubs.most_common(60):
    name = HLE.get(imm & 0xFF, '?')
    if name == '?': unhandled.append(imm)
    vas = stub_va[imm][:2]
    print('  %3d (0x%02X) %-24s x%-4d  e.g. %s' % (imm, imm&0xFF, name, c, ', '.join('0x%08X'%v for v in vas)))

print('\nUnhandled by HLE name table among stubs:', sorted(set(unhandled)))
all_sys=sum(1 for i in range(0,len(text)-4,4) if (struct.unpack_from('<I',text,i)[0] & 0xFC00003F)==0x0000000C)
print('Total raw syscall opcodes:', all_sys)

# FCE0 xrefs
target=0x0010FCE0
enc=0x0C000000 | ((target>>2)&0x3FFFFFF)
pat=struct.pack('<I',enc)
print('\njal 0x0010FCE0 count', text.count(pat))
idx=0
while True:
    j=text.find(pat,idx)
    if j<0: break
    if j%4==0: print('  from 0x%08X'%(LOAD_VA+j))
    idx=j+1

# 51AC80 callers
for tgt,label in [(0x0051AC80,'51AC80'),(0x0051AD80,'51AD80'),(0x00109170,'109170'),(0x0050CFB0,'50CFB0'),(0x004ECD40,'4ECD40')]:
    enc=0x0C000000 | ((tgt>>2)&0x3FFFFFF)
    pat=struct.pack('<I',enc)
    hits=[LOAD_VA+j for j in range(0,len(text)-4,4) if text[j:j+4]==pat]
    # slower - use find
    hits=[]
    idx=0
    while True:
        j=text.find(pat,idx)
        if j<0: break
        if j%4==0: hits.append(LOAD_VA+j)
        idx=j+1
    print('jal 0x%08X (%s) count=%d sites=%s' % (tgt,label,len(hits), hits[:8]))

# imm 0xFCE0
regs=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
print('\naddiu/ori/lui-related imm 0xFCE0:')
for i in range(0,len(text)-4,4):
    w=struct.unpack_from('<I',text,i)[0]
    op=(w>>26)&0x3F
    if op in (8,9,13) and (w&0xFFFF)==0xFCE0:
        rs=(w>>21)&0x1F; rt=(w>>16)&0x1F
        # look back for lui of same rt
        prev=''
        if i>=4:
            p=struct.unpack_from('<I',text,i-4)[0]
            if (p>>26)==15 and ((p>>16)&0x1F)==rt:
                prev=' (after lui %s,0x%04X -> VA 0x%08X)'%(regs[rt], p&0xFFFF, ((p&0xFFFF)<<16)+((w&0xFFFF) if op==13 else struct.unpack('<i',struct.pack('<I',w&0xFFFF if (w&0xFFFF)<0x8000 else (w&0xFFFF)-0x10000))[0] + ((p&0xFFFF)<<16) if False else 0))
                himm=p&0xFFFF
                if op==9:
                    simm=(w&0xFFFF)
                    if simm>=0x8000: simm-=0x10000
                    full=(himm<<16)+simm
                else:
                    full=(himm<<16)|(w&0xFFFF)
                prev=' -> full VA 0x%08X' % (full & 0xFFFFFFFF)
        print('  0x%08X: %s %s,%s,0xFCE0%s' % (LOAD_VA+i, {8:'addi',9:'addiu',13:'ori'}[op], regs[rt], regs[rs], prev))

# strings near 0x610FE0 referenced by main
print('\n=== strings around main refs 0x00610FE0..0x00611050 ===')
for va in range(0x00610FE0, 0x00611100, 4):
    off=FILE_OFF+(va-LOAD_VA)
    # try as C string if printable
    if 32<=data[off]<127:
        end=off
        while end<len(data) and 32<=data[end]<127: end+=1
        if end-off>=4:
            print('0x%08X: %s'%(va, data[off:end].decode()))

# Decode BSS clear range and heap args from CRT0
print('\nBSS clear: v0=0x006F2000 v1=0x0072A480')
print('SetupThread args from CRT0:')
print('  a0/gp = 0x00709BF0')
print('  a1 stack size = 0x01FE0000')
print('  a2 = 0x00020000')
print('  a3 = 0x00729F00')
print('  t0 = 0x00108EF0')

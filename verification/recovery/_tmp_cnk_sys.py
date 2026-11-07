import struct, collections

elf_path = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data = open(elf_path,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80
FILESZ = 0x5F2000
text = data[FILE_OFF:FILE_OFF+FILESZ]

# Scan for syscall (SPECIAL fn=12): word & 0xFC00003F == 0x0000000C
# Gather preceding addiu v1, zero, imm  (opcode 9, rs=0, rt=3): 0x24030000 | imm
# Pattern: often within 8 instructions before syscall

sys_imms = collections.Counter()
sys_sites = []
for i in range(0, len(text)-4, 4):
    w = struct.unpack_from('<I', text, i)[0]
    if (w & 0xFC00003F) == 0x0000000C and ((w >> 6) & 0xFFFFF) == 0:
        # look back up to 8 words for addiu/ori v1
        imm = None
        for back in range(1, 9):
            if i - 4*back < 0: break
            prev = struct.unpack_from('<I', text, i-4*back)[0]
            # addiu v1, zero, simm
            if (prev & 0xFFE00000) == 0x24030000:
                imm16 = prev & 0xFFFF
                if imm16 >= 0x8000: imm16 -= 0x10000
                imm = imm16 & 0xFF  # syscall numbers are small
                # actually keep full
                imm = imm16
                break
            # ori v1, zero, imm
            if (prev & 0xFFE00000) == 0x34030000:
                imm = prev & 0xFFFF
                break
            # lui+ori less common for syscall nums
        va = LOAD_VA + i
        sys_imms[imm] += 1
        if len(sys_sites) < 5 or (imm is not None and imm in (16,54,55,60,61,0x74,0x5A,0x5B)):
            sys_sites.append((va, imm))

print('syscall count', sum(sys_imms.values()))
print('Top v1 immediates:')
for imm,c in sys_imms.most_common(40):
    print('  %s : %d' % (('None' if imm is None else '0x%X (%d)' % (imm & 0xFFFFFFFF, imm)), c))

# Also find CreateSema-like: syscall after v1=0x16 (22 CreateSema) or wrappers
# EE kernel: CreateSema=22, DeleteSema=23, SignalSema=24, WaitSema=25, PollSema=26, ReferSemaStatus=27
EE = {
  1:'ResetEE',2:'SetGsCrt',4:'Exit',5:'_ExceptionEpilogue',6:'LoadExecPS2',7:'ExecPS2',
  16:'AddSbusIntcHandler',17:'RemoveSbusIntcHandler',18:'Interrupt2Iop',
  19:'SetVSyncFlag',20:'SetSyscall',22:'CreateSema',23:'DeleteSema',24:'SignalSema',
  25:'WaitSema',26:'PollSema',27:'ReferSemaStatus',28:'iSignalSema',29:'iWaitSema',
  30:'CreateThread',31:'DeleteThread',32:'StartThread',33:'ExitThread',34:'ExitDeleteThread',
  35:'TerminateThread',36:'iTerminateThread',37:'DisableDispatchThread',38:'EnableDispatchThread',
  39:'ChangeThreadPriority',40:'iChangeThreadPriority',41:'RotateThreadReadyQueue',
  43:'ReleaseWaitThread',44:'iReleaseWaitThread',45:'GetThreadId',46:'ReferThreadStatus',
  47:'iReferThreadStatus',48:'SleepThread',49:'WakeupThread',50:'iWakeupThread',
  51:'CancelWakeupThread',52:'iCancelWakeupThread',53:'SuspendThread',54:'iSuspendThread',
  55:'ResumeThread',56:'iResumeThread',57:'JoinThread',60:'SetupThread',61:'SetupHeap',
  62:'EndOfHeap',64:'CreateSema', # wait CreateSema is 22
  0x40:'CreateSema_alt?',
  100:'SifStopDma',116:'SifSetDma',117:'SifSetDChain',118:'SifSetReg',119:'SifGetReg',
  120:'ExecPS2', # 
}
# Correct SCE EE syscall numbers (ps2tek / kernel):
EE_NAMES = {
0x01:'ResetEE',0x02:'SetGsCrt',0x04:'Exit',0x05:'_ExceptionEpilogue',0x06:'LoadExecPS2',0x07:'ExecPS2',
0x10:'AddSbusIntcHandler',0x11:'RemoveSbusIntcHandler',0x12:'Interrupt2Iop',0x13:'SetVSyncFlag',0x14:'SetSyscall',
0x16:'CreateSema',0x17:'DeleteSema',0x18:'SignalSema',0x19:'WaitSema',0x1A:'PollSema',0x1B:'ReferSemaStatus',
0x1C:'iSignalSema',0x1D:'iWaitSema?',
0x1E:'CreateThread',0x1F:'DeleteThread',0x20:'StartThread',0x21:'ExitThread',0x22:'ExitDeleteThread',
0x23:'TerminateThread',0x24:'iTerminateThread',
0x29:'ChangeThreadPriority',0x2A:'iChangeThreadPriority',0x2B:'RotateThreadReadyQueue',
0x2D:'ReleaseWaitThread',0x2E:'iReleaseWaitThread',0x2F:'GetThreadId',0x30:'ReferThreadStatus',
0x31:'iReferThreadStatus',0x32:'SleepThread',0x33:'WakeupThread',0x34:'iWakeupThread',
0x35:'CancelWakeupThread',0x36:'iCancelWakeupThread',0x37:'SuspendThread',0x38:'iSuspendThread',
0x39:'ResumeThread',0x3A:'iResumeThread',0x3B:'JoinThread',
0x3C:'SetupThread',0x3D:'SetupHeap',0x3E:'EndOfHeap',
0x3F:'CreateSema', # NO - CreateSema is 0x16
0x40:'DeleteSema_dup?',
0x74:'SifSetDma',0x75:'SifSetDChain',0x76:'SifSetReg',0x77:'SifGetReg',
0x5A:'SifDmaStat?',0x5B:'?',
0x7A:'Deci2Call',0x7E:'MachineType',0x7F:'GetMemorySize',
}
print('\nNamed mapping of top:')
for imm,c in sys_imms.most_common(30):
    if imm is None:
        print('  unresolved: %d' % c); continue
    name = EE_NAMES.get(imm & 0xFF, EE_NAMES.get(imm, '?'))
    print('  %d (0x%X) %s : %d' % (imm, imm & 0xFFFFFFFF, name, c))

# Find hardcoded WaitSema with a0 = 16/54/55
print('\n=== addiu a0, zero, {16,54,55} near syscall / jal patterns ===')
for target in (16,54,55):
    # addiu a0, zero, N = 0x24040000 | (N & 0xFFFF)
    pat = struct.pack('<I', 0x24040000 | (target & 0xFFFF))
    count=0
    sites=[]
    start=0
    while True:
        i=text.find(pat, start)
        if i<0: break
        if i%4==0:
            va=LOAD_VA+i
            # peek next few for syscall or jal
            nxt=[]
            for k in range(1,6):
                if i+4*k+4<=len(text):
                    nw=struct.unpack_from('<I',text,i+4*k)[0]
                    nxt.append('%08X'%nw)
            sites.append((va, nxt))
            count+=1
        start=i+1
    print('a0=%d count=%d' % (target, count))
    for va,nxt in sites[:15]:
        print('  0x%08X  next=%s' % (va, ' '.join(nxt)))

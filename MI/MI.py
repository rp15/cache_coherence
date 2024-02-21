class CPU:
    def __init__(self, nr):
        self.nr               = nr
        self.cacheEntries     = 0
        self.cacheEntryVal    = []
        self.cacheEntryStatus = []
        self.cacheSize        = 2

    def addBlock(self, blkAddr):
        # TODO Have to check for hit (blkAddr already in cache) before adding new item.
        if self.cacheEntries < self.cacheSize:
            self.cacheEntryVal.append(blkAddr)
            self.cacheEntryStatus.append('M')
            self.cacheEntries += 1
        #else:
            # TODO if cache is full, need a replacement.

    def updateBlock(self, blkAddr):
        for i in range( len(self.cacheEntryVal) ):
            if blkAddr == self.cacheEntryVal[i]:
                self.cacheEntryStatus[i] = 'I'

    # These need to modify other CPUs and directory, so maybe not appropriate as CPU member fn.
    #def CPURead(self, blkAddr):

    #def CPURead(self, blkAddr):

class directory:
    def __init__(self):
        self.entries = {}
        self.dirty   = {}

    def accessBlock(self, blkAddr, requestor):
        self.dirty.update({blkAddr: 1})
        self.entries.update( {blkAddr: ( (1 == requestor), (0 == requestor) )} )

#def dataAccess(CPU, blkAddr, dir):
#    CPU.addBlock(blkAddr)
#    dir.accessBlock(blkAddr, CPU.nr)
#    CPU1.updateBlock(0) TODO In a foreach loop, issue this cmd for all CPUs that are set to one/True in the corresponding line in the directory.

CPU0 = CPU(0)
CPU1 = CPU(1)

dir = directory()

# 1) CPU0 RD 0
CPU0.addBlock(0)
dir.accessBlock(0, 0)
CPU1.updateBlock(0) # Should not matter here, this could be called based on looking at the previous cmd, if it had CPU1 listed as containing blkAddr0, then call this.
print(dir.entries)
print('\n')

# 2) CPU1 WR 2
CPU1.addBlock(2)
dir.accessBlock(2, 1)
CPU0.updateBlock(2) # Irrelevant like above, CPU 0 does not have blkAddr 2.
print(dir.entries)
print('\n')

# 3) CPU1 RD 1
CPU1.addBlock(1)
dir.accessBlock(1, 1)
CPU0.updateBlock(1) # Still irrelevant like above, CPU 0 does not have blkAddr 1.
print(dir.entries)
print('\n')

# 4) CPU0 RD 1
CPU0.addBlock(1)
dir.accessBlock(1, 0)
CPU1.updateBlock(1) # Now it is needed, since CPU1 had blkAddr 1 in 'M' state.
print(dir.entries)
print('\n')

# 5) CPU1 WR 1 TODO CPU1 already has blkAddr though in 'I' state. This would need to replace that, needs to be implemented in CPU logic.


import sys
import transactions_pb2

if len(sys.argv) != int(sys.argv[1]) + 2:
  print("Usage:", sys.argv[0], "TX_FILE0 TX_FILE1 ...")
  print("The specified nr of nodes does not match the number of provided tx files.")
  sys.exit(-1)

class CPU:
    def __init__(self, nr):
        self.nr               = nr
        self.cacheEntries     = 0
        self.cacheEntryVal    = []
        self.cacheEntryStatus = []
        self.cacheSize        = 999

    def addBlock(self, blkAddr):
        # Check for hit (blkAddr already in cache) before adding new item.
        present = 0
        for i in range( len(self.cacheEntryVal) ):
            if blkAddr == self.cacheEntryVal[i]:
                present = 1
                self.cacheEntryStatus[i].updateStatus('M')
                break
        if not present and self.cacheEntries < self.cacheSize:
            self.cacheEntryVal.append(blkAddr)
            self.cacheEntryStatus.append( status('M') )
            self.cacheEntries += 1
        elif self.cacheEntries >= self.cacheSize:
            # TODO if cache is full, need a replacement.
            print("Error: Cache should not fill up, assuming infinite size for this simulation.\n")

    def updateBlock(self, blkAddr):
        # Find the block to update.
        for i in range( len(self.cacheEntryVal) ):
            if blkAddr == self.cacheEntryVal[i]:
                self.cacheEntryStatus[i].updateStatus('I')

    # These need to modify other CPUs and directory, so maybe not appropriate as CPU member fn.
    #def CPURead(self, blkAddr):

    #def CPURead(self, blkAddr):

class directory:
    def __init__(self):
        self.entries = {}
        self.dirty   = {}

    def accessBlock(self, blkAddr, requestor, nodes):
        self.dirty.update({blkAddr: 1})
        arrayOfNodes = []
        for i in range( len(nodes) ):
            if requestor == i:
                arrayOfNodes.append(1);
            else:
                arrayOfNodes.append(0);
        self.entries.update( {blkAddr: arrayOfNodes} )
        #self.entries.update( {blkAddr: ( (1 == requestor), (0 == requestor) )} )

class status:
    def __init__(self):
        self.status = 'I'

    def __init__(self, status):
        self.status = status

    def updateStatus(self, status):
        self.status = status

class message:
    def __init__(self):
        self.text = "[CC protocol] Test.\n"

def dataAccess(nodes, CPUIdx, blkAddr, dir):
    nodes[CPUIdx].addBlock(blkAddr)
    dir.accessBlock(blkAddr, CPUIdx, nodes)
    #CPU1.updateBlock(0)
    # In a foreach loop, issue this cmd for all CPUs that are set to one/True in the corresponding line in the directory.
    for i in range( len( dir.entries[blkAddr] ) ):
        if 1 == dir.entries[blkAddr][i] and i != CPUIdx:
            nodes[i].updateBlock(blkAddr)
            #dir.entries[blkAddr][i] = 0


# Instantiate nodes and directory.
nodes = []
for i in range( int(sys.argv[1]) ):
    nodes.append( CPU(i) )

#nodes.append( CPU(0) )
#nodes.append( CPU(1) )
#nodes.append( CPU(2) )

dir = directory()

txs = []
total_txs = 0

for i in range( int(sys.argv[1]) ):
    txs.append( transactions_pb2.Transaction_list() )

    with open(sys.argv[i + 2], "rb") as f:
        txs[i].ParseFromString(f.read())

    total_txs += len(txs[i].transactions)
    #print(txs[i])

#print(total_txs)

# TODO Go thru all txs and pick the next-highest-tick one.
# TODO Currently assuming that ticks are uniquely incremented by one across all txs (1 .. total_txs).
latest_tick = 0
for i in range(total_txs):
    for j in range( len(txs) ):
        for tx in txs[j].transactions:
            if tx.tick == i + 1:
                dataAccess(nodes, tx.nodeID, tx.blkAddr, dir)
                latest_tick = tx.tick
                print(tx)
                print(dir.dirty, dir.entries)

# 1) CPU0 RD 0
#dataAccess(nodes, 0, 0, dir)
#print(dir.dirty, dir.entries)

# 2) CPU1 WR 2
#dataAccess(nodes, 1, 2, dir)
#print(dir.dirty, dir.entries)

# 3) CPU1 RD 1
#dataAccess(nodes, 1, 1, dir)
#print(dir.dirty, dir.entries)

# 4) CPU0 RD 1
#dataAccess(nodes, 0, 1, dir)
#print(dir.dirty, dir.entries)

# 5) CPU1 WR 1 TODO CPU1 already has blkAddr though in 'I' state. This would need to replace that, needs to be implemented in CPU logic.
#dataAccess(nodes, 1, 1, dir)
#print(dir.dirty, dir.entries)

# 6) CPU2 RD 1
#dataAccess(nodes, 2, 1, dir)
#print(dir.dirty, dir.entries)


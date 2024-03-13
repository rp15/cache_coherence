import sys
import transactions_pb2

if len(sys.argv) != int(sys.argv[1]) + 2:
  print("Usage:", sys.argv[0], "TX_FILE0 TX_FILE1 ...")
  print("The specified nr of nodes does not match the number of provided tx files.")
  sys.exit(-1)

tracker = []
for i in range( int(sys.argv[1]) ):
    tracker.append(0)

MEMORY_RD = 4
DATA_FWD  = 1

class CPU:
    def __init__(self, nr):
        self.nr               = nr
        self.cacheEntries     = 0
        self.cacheEntryVal    = []
        self.cacheSize        = 999

    def addBlock(self, blkAddr, designatedCPU):
        presentInDesignatedNode = 0
        for i in range( len(designatedCPU.cacheEntryVal) ):
            if blkAddr == designatedCPU.cacheEntryVal[i]:
                presentInDesignatedNode = 1
                break
        # Check for hit (blkAddr already in cache) before adding new item.
        present = 0
        if self == designatedCPU and presentInDesignatedNode:
            # Already has the data (and not in invalid state).
            tracker[self.nr] += 0
        elif self != designatedCPU and presentInDesignatedNode:
            tracker[self.nr] += DATA_FWD
        elif not presentInDesignatedNode:
            # Needs a memory access.
            tracker[self.nr] += MEMORY_RD

        if not presentInDesignatedNode and self.cacheEntries < self.cacheSize:
            designatedCPU.cacheEntryVal.append(blkAddr)
            designatedCPU.cacheEntries += 1
        elif self.cacheEntries >= self.cacheSize:
            # TODO if cache is full, need a replacement.
            print("Error: Cache should not fill up, assuming infinite size for this simulation.\n")


class message:
    def __init__(self):
        self.text = "[CC protocol] Test.\n"

def dataAccess(nodes, CPUIdx, blkAddr):
    nodes[CPUIdx].addBlock( blkAddr, nodes[ blkAddr % int(sys.argv[1]) ] )


# Instantiate nodes and directory.
nodes = []
for i in range( int(sys.argv[1]) ):
    nodes.append( CPU(i) )


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
                dataAccess(nodes, tx.nodeID, tx.blkAddr)
                latest_tick = tx.tick
                print(tx)
                print(tracker)
                print("\n")

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

print(tracker)


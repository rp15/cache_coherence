import sys
import argparse
import transactions_pb2

parser = argparse.ArgumentParser(
                    prog='MESI',
                    description='MESI simulator.',
                    epilog='RJ.')

parser.add_argument('-n', '--node_count', required=True, type=int)
parser.add_argument('-c', '--cache_line_size_bytes', default=32, type=int)

parser.add_argument('-r', '--read_penalty', default=800, type=int)
parser.add_argument('-f', '--forwarding_penalty', default=9, type=int)

#parser.add_argument('-i', '--input_transaction_file', nargs='+')
parser.add_argument('-i', '--input_transaction_file', required=True, action='append')

args = parser.parse_args()

node_count              = args.node_count
cache_line_size_bytes   = args.cache_line_size_bytes
input_transaction_files = args.input_transaction_file


if len(input_transaction_files) != node_count:
  print("The specified nr of nodes does not match the number of provided txn files.")
  sys.exit(-1)


tracker = []
for i in range(node_count):
    tracker.append(0)

MEMORY_RD = args.read_penalty
DATA_FWD  = args.forwarding_penalty

class CPU:
    def __init__(self, nr):
        self.nr               = nr
        self.cacheEntries     = 0
        self.cacheEntryVal    = []
        self.cacheEntryStatus = []
        self.cacheSize        = 999

    # When this node is accessing (rd or wr) a blk, call this fn to maintain the cache.
    def addBlock(self, blkAddr, dir, rdNWr):
        presentInOtherNode = 0
        if blkAddr in dir.entries:
            for i in range( len(dir.entries[blkAddr]) ):
                if 1 == dir.entries[blkAddr][i] and i != self.nr:
                    presentInOtherNode = 1
                    break
        # Check for hit (blkAddr already in cache) before adding new item.
        present = 0
        for i in range( len(self.cacheEntryVal) ):
            if blkAddr == self.cacheEntryVal[i]:
                present = 1
                if 'I' == self.cacheEntryStatus[i].status:
                    if not presentInOtherNode:
                        # Needs a memory access.
                        tracker[self.nr] += MEMORY_RD
                    else:
                        tracker[self.nr] += DATA_FWD
                #elif M, E, or S; no mem access necessary.
# TODO cont here.
                if 1 == rdNWr:
                    # If any other node has this data, make it 'S,' otherwise 'E.'
                    if presentInOtherNode:
                        self.cacheEntryStatus[i].updateStatus('S')
                    else:
                        self.cacheEntryStatus[i].updateStatus('E')
                else: # Write.
                    self.cacheEntryStatus[i].updateStatus('M')
                break
        if not present and self.cacheEntries < self.cacheSize:
            self.cacheEntryVal.append(blkAddr)
            if 1 == rdNWr:
                # If any other node has this data, make it 'S,' otherwise 'E.'
                if presentInOtherNode:
                    self.cacheEntryStatus.append( status('S') )
                else:
                    self.cacheEntryStatus.append( status('E') )
            else: # Write.
                self.cacheEntryStatus.append( status('M') )
            self.cacheEntries += 1
            if not presentInOtherNode:
                # Needs a memory access.
                tracker[self.nr] += MEMORY_RD
            else:
                tracker[self.nr] += DATA_FWD
        elif self.cacheEntries >= self.cacheSize:
            # TODO if cache is full, need a replacement.
            print("Error: Cache should not fill up, assuming infinite size for this simulation.\n")

    # When some other node is accessing a blk, call this fn to update other nodes' status.
    def updateBlock(self, blkAddr, rdNWr):
        # Find the block to update.
        for i in range( len(self.cacheEntryVal) ):
            if blkAddr == self.cacheEntryVal[i]:
                if 1 == rdNWr:
                    # TODO If I was 'I' when someone else read this blk, do I stay in 'I' or snoop it and go to 'S'?
                    # TODO Update MI and MSI accordingly as well.
                    self.cacheEntryStatus[i].updateStatus('S')
                else:
                    self.cacheEntryStatus[i].updateStatus('I')

    # These need to modify other CPUs and directory, so maybe not appropriate as CPU member fn.
    #def CPURead(self, blkAddr):

    #def CPURead(self, blkAddr):

class directory:
    def __init__(self):
        self.entries = {}
        self.dirty   = {}

    def accessBlock(self, blkAddr, requestor, nodes, rdNWr):
        if 1 == rdNWr:
            self.dirty.update({blkAddr: 0})
        else:
            self.dirty.update({blkAddr: 1})
        arrayOfNodes = []
        # If it is a RD and the blkAddr is already in the directory, leave the entry as is and add the RDing node as S/E.
        if 1 == rdNWr and blkAddr in self.entries.keys():
            self.entries[blkAddr][requestor] = 1
        # If it is a WR or a new blkAddr, only the accessing CPU will have the blkAddr in its cache.
        else:
            for i in range( len(nodes) ):
                if requestor == i:
                    arrayOfNodes.append(1);
                else:
                    arrayOfNodes.append(0);
            self.entries.update( {blkAddr: arrayOfNodes} )

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

def dataAccess(nodes, CPUIdx, blkAddr, dir, rdNWr):
    nodes[CPUIdx].addBlock(blkAddr, dir, rdNWr)
    if blkAddr in dir.entries.keys():
        tempDirEntry = dir.entries[blkAddr]
        newDirEntry = 0
    else:
        newDirEntry = 1
    dir.accessBlock(blkAddr, CPUIdx, nodes, rdNWr)
    #CPU1.updateBlock(0)
    # (If not a new dir entry,) in a foreach loop, issue this cmd for all CPUs that are set to one/True in the corresponding line in the directory.
    if not newDirEntry:
        for i in range( len( dir.entries[blkAddr] ) ):
            if 1 == tempDirEntry[i] and i != CPUIdx:
                nodes[i].updateBlock(blkAddr, rdNWr)


# Instantiate nodes and directory.
nodes = []
for i in range(node_count):
    nodes.append( CPU(i) )

#nodes.append( CPU(0) )
#nodes.append( CPU(1) )
#nodes.append( CPU(2) )

dir = directory()

txs = []
total_txs = 0

for i in range(node_count):
    txs.append( transactions_pb2.Transaction_list() )

    with open(input_transaction_files[i], "rb") as f:
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
            if tx.tick == i:
                dataAccess( nodes, tx.nodeID, int(tx.memAddr / cache_line_size_bytes), dir, tx.direction )
                latest_tick = tx.tick
                print("Time tick (i.e., txn ID):    ", tx.tick,
                    "\nNode ID:                     ", tx.nodeID,
                    "\nTxn memory address:          ", tx.memAddr,
                    "\nTxn block address:           ", int(tx.memAddr / cache_line_size_bytes),
                    "\nTxn direction:               ", "RD" if tx.direction else "WR")
                print("Directory dirty, entries:    ", dir.dirty, dir.entries)
                print("Current txn penalty per node:", tracker, "\n")


# 1) CPU0 RD 0
#dataAccess(nodes, 0, 0, dir, 1)
#print(dir.dirty, dir.entries)
# 1) CPU0 RD 0
#dataAccess(nodes, 0, 0, dir, 1)
#print(dir.dirty, dir.entries)

# 2) CPU1 WR 2
#dataAccess(nodes, 1, 2, dir, 0)
#print(dir.dirty, dir.entries)

# 3) CPU1 RD 1
#dataAccess(nodes, 1, 1, dir, 1)
#print(dir.dirty, dir.entries)

# 4) CPU0 RD 1
#dataAccess(nodes, 0, 1, dir, 1)
#print(dir.dirty, dir.entries)

# 5) CPU1 WR 1 TODO CPU1 already has blkAddr though in 'I' state. This would need to replace that, needs to be implemented in CPU logic.
#dataAccess(nodes, 1, 1, dir, 0)
#print(dir.dirty, dir.entries)

# 6) CPU2 RD 1
#dataAccess(nodes, 2, 1, dir, 1)
#print(dir.dirty, dir.entries)

#print(tracker)


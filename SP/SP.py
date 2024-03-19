import sys
import argparse
import transactions_pb2

parser = argparse.ArgumentParser(
                    prog='SP',
                    description='Scratchpad simulator.',
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
    # The blkAddr is stored in the node purely based on its address.
    # For three nodes, Node0 stores addr 0, 3, 6, .., Node 1 stores addr 1, 4, 7, .., etc.
    nodes[CPUIdx].addBlock( blkAddr, nodes[blkAddr % node_count] )


# Instantiate nodes and directory.
nodes = []
for i in range(node_count):
    nodes.append( CPU(i) )


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
                dataAccess( nodes, tx.nodeID, int(tx.memAddr / cache_line_size_bytes) )
                latest_tick = tx.tick
                print("Time tick (i.e., txn ID):    ", tx.tick,
                    "\nNode ID:                     ", tx.nodeID,
                    "\nTxn memory address:          ", tx.memAddr,
                    "\nTxn block address:           ", int(tx.memAddr / cache_line_size_bytes),
                    "\nTxn direction:               ", "RD" if tx.direction else "WR")
                print("Current txn penalty per node:", tracker, "\n")

#print(tracker)

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


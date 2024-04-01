import sys
import argparse
import transactions_pb2

parser = argparse.ArgumentParser(
                    prog='MI',
                    description='MI simulator.',
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

    def addBlock(self, blkAddr, dir):
        presentInOtherNode = 0
        if blkAddr in dir.entries:
            for i in range( len(dir.entries[blkAddr]) ):
                if 1 == dir.entries[blkAddr][i] and i != self.nr:
                    presentInOtherNode = 1
                    break
        # Check for hit (blkAddr already in cache) before adding new item.
        present = 0
        #print(self.nr, self.cacheEntryVal, self.cacheEntryStatus, tracker)
        for i in range( len(self.cacheEntryVal) ):
            if blkAddr == self.cacheEntryVal[i]:
                present = 1
                if 'I' == self.cacheEntryStatus[i].status:
                    if not presentInOtherNode:
                        # Needs a memory access.
                        tracker[self.nr] += MEMORY_RD
                    else:
                        tracker[self.nr] += DATA_FWD
                elif 'M' == self.cacheEntryStatus[i].status:
                    # Already has the data (and not in invalid state).
                    tracker[self.nr] += 0
                self.cacheEntryStatus[i].updateStatus('M')
                break
        if not present and self.cacheEntries < self.cacheSize:
            self.cacheEntryVal.append(blkAddr)
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
    nodes[CPUIdx].addBlock(blkAddr, dir)
    dir.accessBlock(blkAddr, CPUIdx, nodes)
    # In a foreach loop, issue this cmd for all CPUs that are set to one/True in the corresponding line in the directory.
    for i in range( len(nodes) ):
        # dir.accessBlock already cleared the old status in the dir. But we know that for MI, everybody else goes 'I.'
        #if 1 == dir.entries[blkAddr][i] and i != CPUIdx:
        if i != CPUIdx:
            nodes[i].updateBlock(blkAddr)
            #dir.entries[blkAddr][i] = 0


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
    # Add an empty txn list to the array for every node.
    txs.append( transactions_pb2.Transaction_list() )

    # Populate the txn list from the node's txn-list txt file.
    with open(input_transaction_files[i], "rb") as f:
        txs[i].ParseFromString(f.read())

    # Increase the total nr of txns by the node's txn cnt.
    total_txs += len(txs[i].transactions)
    #print(txs[i])

#print(total_txs)

# TODO Go thru all txs and pick the next-highest-tick one.
# TODO Currently assuming that ticks are uniquely incremented by one across all txs (1 .. total_txs).
#latest_tick = 0
#for i in range(total_txs):
#    for j in range( len(txs) ):
#        for tx in txs[j].transactions:
#            if tx.tick == i:
#                dataAccess( nodes, tx.nodeID, int(tx.memAddr / cache_line_size_bytes), dir )
#                latest_tick = tx.tick
#                print("Time tick (i.e., txn ID):    ", tx.tick,
#                    "\nNode ID:                     ", tx.nodeID,
#                    "\nTxn memory address:          ", tx.memAddr,
#                    "\nTxn block address:           ", int(tx.memAddr / cache_line_size_bytes),
#                    "\nTxn direction:               ", "RD" if tx.direction else "WR")
#                print("Directory dirty, entries:    ", dir.dirty, dir.entries)
#                print("Current txn penalty per node:", tracker, "\n")

txn_executed = []
hiest_tick = 0
for j in range( len(txs) ):
    txn_executed.append([])
    for k in range( len(txs[j].transactions) ):
        txn_executed[j].append(0)
        if txs[j].transactions[k].tick > hiest_tick:
            hiest_tick = txs[j].transactions[k].tick

print(txn_executed)

candidate_tick       = -1
latest_executed_tick =  0

for i in range(total_txs):
    candidate_tick = hiest_tick
    for j in range( len(txs) ):
        for k in range( len(txs[j].transactions) ): # for tx in txs[j].transactions:
            tx = txs[j].transactions[k]
            if not txn_executed[j][k] and tx.tick >= latest_executed_tick and tx.tick <= candidate_tick:
                candidate_tick         = tx.tick
                nxt_txn_node           = j
                nxt_txn_id_within_node = k

    tx_current = txs[nxt_txn_node].transactions[nxt_txn_id_within_node]
    dataAccess( nodes, tx_current.nodeID, int(tx_current.memAddr / cache_line_size_bytes), dir )
    latest_executed_tick = tx_current.tick
    txn_executed[nxt_txn_node][nxt_txn_id_within_node] = 1

    print("Time tick (i.e., txn ID):    ", tx_current.tick,
        "\nNode ID:                     ", tx_current.nodeID,
        "\nTxn memory address:          ", tx_current.memAddr,
        "\nTxn block address:           ", int(tx_current.memAddr / cache_line_size_bytes),
        "\nTxn direction:               ", "RD" if tx_current.direction else "WR")
    print("Directory dirty, entries:    ", dir.dirty, dir.entries)
    print("Current txn penalty per node:", tracker, "\n")
print(txn_executed)
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

#print(tracker)


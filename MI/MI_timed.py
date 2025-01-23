import sys
import argparse
import transactions_pb2
from queue import PriorityQueue
from itertools import count

# python3.12 MI/MI_timed.py -n 3 -c 1 -r 4 -f 1 -d 1 -i MI/node0.txt -i MI/node1.txt -i MI/node2.txt

parser = argparse.ArgumentParser(
                    prog='MI',
                    description='MI simulator.',
                    epilog='RJ.')

parser.add_argument('-n', '--node_count', required=True, type=int)
parser.add_argument('-c', '--cache_line_size_bytes', default=32, type=int)

parser.add_argument('-r', '--read_penalty', default=800, type=int)
parser.add_argument('-f', '--forwarding_penalty', default=9, type=int)

parser.add_argument('-d', '--dram_rd_port_cnt', default=1, type=int)

#parser.add_argument('-i', '--input_transaction_file', nargs='+')
parser.add_argument('-i', '--input_transaction_file', required=True, action='append')

args = parser.parse_args()

node_count              = args.node_count
cache_line_size_bytes   = args.cache_line_size_bytes
input_transaction_files = args.input_transaction_file
dram_rd_port_cnt        = args.dram_rd_port_cnt


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

    def readRequired(self, blkAddr, dir):
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
                        return True
                break
        if not present and self.cacheEntries < self.cacheSize:
            if not presentInOtherNode:
                # Needs a memory access.
                return True
        return False

    def fwdRequired(self, blkAddr, dir):
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
                    if presentInOtherNode:
                        return True
                break
        if not present and self.cacheEntries < self.cacheSize:
            if presentInOtherNode:
                return True
        return False

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
        self.entries  = {}
        self.dirty    = {}
        self.expected = {}
        self.req_node = {}

    def accessBlock(self, blkAddr, requestor, nodes):
        self.dirty.update({blkAddr: 1})
        arrayOfNodes = []
        for i in range( len(nodes) ):
            if requestor == i:
                arrayOfNodes.append(1)
            else:
                arrayOfNodes.append(0)
        self.entries.update( {blkAddr: arrayOfNodes} )
        if requestor == self.req_node[blkAddr]: # If the executed tx's node is the last one who was requesting this block (no future fwding), then clear that info.
            self.expected.update( {blkAddr: -1} ) # -1 (not a real time tick) means that the block is actually in the directory and no one is waiting for it.
            self.req_node.update( {blkAddr: -1} ) # -1 (not a real node) means that the block is actually in the directory and no one is waiting for it.

    def expectBlock(self, blkAddr, requestor, tick):
        self.req_node.update( {blkAddr: requestor} )
        self.expected.update( {blkAddr: tick} )



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


dram_port_started_read = []
dram_port_reading_block = []
waiting_for_dram_port  = []

for i in range(dram_rd_port_cnt):
    dram_port_started_read.append(-MEMORY_RD)
    dram_port_reading_block.append(-1)


# Go thru all txs and pick the next-highest-tick one (or same as last one if
# there are multiple events at the same tick).
txn_executed = []
txn_ordered = []
hiest_tick = 0

# Create an array to store tx execution status and find the hiest tick
# at the same time.
for j in range( len(txs) ):
    txn_executed.append([])
    txn_ordered.append([])
    for k in range( len(txs[j].transactions) ):
        txn_executed[j].append(0)
        txn_ordered[j].append(0)
        if txs[j].transactions[k].tick > hiest_tick:
            hiest_tick = txs[j].transactions[k].tick

candidate_tick       = -1
latest_executed_tick =  0

# Maybe not used:
tx_list_to_execute   = {} # Key: time tick, Value: array of txns that can happen at that time (in order).


# Priority queues per node, ordered by tick.
nodeNQ = []

# Wrapper to avoid comparing txn objects.
class TxnWrapper:
    def __init__(self, priority, item):
        self.priority = priority
        self.item = item

    def __lt__(self, other):
        return self if self.priority < other.priority else other

for i in range(node_count):
    nodeNQ.append( PriorityQueue() )
    for j in range( len(txs[i].transactions) ):
        nodeNQ[i].put( TxnWrapper(txs[i].transactions[j].tick, txs[i].transactions[j]) )


# Global priority queue holding the head of each per-node priority queue, ordered by tick.
globalQ = PriorityQueue()

# Execute txns.
while True:
    for i in range(node_count):
        if not nodeNQ[i].empty():
            tmp_tx = nodeNQ[i].get().item
            globalQ.put( TxnWrapper(tmp_tx.tick, tmp_tx) )
    if globalQ.empty():
        break # Done executing.

    # Run execution, putting back txn items in the individual queues if necessary.
    # We know at this point, it is not empty. Getting the earliest non-executed tx.
    tx_to_test = globalQ.get().item

    # Either execute it successfully or put it back in the respective individual queue with its new time tick.
    # Have to check if a) this tx needs a mem read or b) mem forward.
    ##########
    # RD REQ #
    ##########
    if nodes[tx_to_test.nodeID].readRequired( int(tx_to_test.memAddr / cache_line_size_bytes), dir ):
        #####
        # 1 #
        #####
        # If another node is already doing a read (if tick is not smaller, otherwise would probably need a fwd).
        if int(tx_to_test.memAddr / cache_line_size_bytes) in dir.expected and dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] > tx_to_test.tick and tx_to_test.nodeID != dir.req_node[ int(tx_to_test.memAddr / cache_line_size_bytes) ]:
            # Put the tx back in its individual queue with the forwarded time tick.
            tx_to_test.tick = dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] + DATA_FWD
            nodeNQ[tx_to_test.nodeID].put( TxnWrapper(tx_to_test.tick, tx_to_test) )
        #####
        # 2 # less than not going to happen. Equal can happen, meaning in the same cycle, the reading node will finish the read and we should be able to fwd.
        #####
        # If another node already finished a read/fwd and we still require a read instead of a fwd,
        # meaning the block got lost somehow (evicted?), plan the read.
        # This might not happen since the earlier node's actual read would've cleared the expected field.
        elif int(tx_to_test.memAddr / cache_line_size_bytes) in dir.expected and dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] <= tx_to_test.tick and tx_to_test.nodeID != dir.req_node[ int(tx_to_test.memAddr / cache_line_size_bytes) ]:
            tx_to_test.tick += DATA_FWD
            nodeNQ[tx_to_test.nodeID].put( TxnWrapper(tx_to_test.tick, tx_to_test) )
        #####
        # 3 #
        #####
        # Plan the read if the block is not recorded in the dir.
        elif int(tx_to_test.memAddr / cache_line_size_bytes) not in dir.expected:
            tx_to_test.tick += MEMORY_RD
            nodeNQ[tx_to_test.nodeID].put( TxnWrapper(tx_to_test.tick, tx_to_test) )
            #dir.req_node[ int(tx_to_test.memAddr / cache_line_size_bytes) ] = tx_to_test.nodeID
            #dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] = tx_to_test.tick + MEMORY_READ
            dir.expectBlock(int(tx_to_test.memAddr / cache_line_size_bytes), tx_to_test.nodeID, tx_to_test.tick)
        #####
        # 4 #
        #####
        # If this node is reading the same block already, try this txn again when the read is complete.
        # (same sounds good if the unique ctr will guarantee that this subsequent tx is attempted after the one already in the queue: or 1 tick later to let the original read take effect, maybe a bug if there are other txns following right after as well).
        elif int(tx_to_test.memAddr / cache_line_size_bytes) in dir.expected and dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] > tx_to_test.tick and tx_to_test.nodeID == dir.req_node[ int(tx_to_test.memAddr / cache_line_size_bytes) ]:
            tx_to_test.tick = dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] #+ 1
            nodeNQ[tx_to_test.nodeID].put( TxnWrapper(tx_to_test.tick, tx_to_test) )
        #####
        # 5 #
        #####
        # If this node has read the same block already but a read is required, meaning it lost it somehow
        # OR WE JUST CAME BACK TO ACTUALLY execute the read, which one? Execute/plan the read.
        elif int(tx_to_test.memAddr / cache_line_size_bytes) in dir.expected and dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] <= tx_to_test.tick and tx_to_test.nodeID == dir.req_node[ int(tx_to_test.memAddr / cache_line_size_bytes) ]:
            #tx_to_test.tick += MEMORY_RD
            #nodeNQ[tx_to_test.nodeID].put( TxnWrapper(tx_to_test.tick, tx_to_test) )
            #dir.expectBlock(int(tx_to_test.memAddr / cache_line_size_bytes), tx_to_test.nodeID, tx_to_test.tick)
            dataAccess( nodes, tx_to_test.nodeID, int(tx_to_test.memAddr / cache_line_size_bytes), dir )

    ###########
    # FWD REQ #
    ###########
    # Nothing fancy here just put back with expected + FWD_PENALTY?
    # TODO if it already passed the time tick where the read + FWD was supposed to be ready, we can actually do dataAccess()?
    elif nodes[tx_to_test.nodeID].fwdRequired ( int(tx_to_test.memAddr / cache_line_size_bytes), dir ):
        tx_to_test.tick = dir.expected[ int(tx_to_test.memAddr / cache_line_size_bytes) ] + DATA_FWD
        nodeNQ[tx_to_test.nodeID].put( TxnWrapper(tx_to_test.tick, tx_to_test) )
    # TODO, if nothing is required, execute it! Read or fwd should probably be required for something meaningful to happen?

    ##########
    # NO REQ #
    ##########
    else:
       dataAccess( nodes, tx_to_test.nodeID, int(tx_to_test.memAddr / cache_line_size_bytes), dir )
    

    # Empty the global queue back to the individual queues.
    while not globalQ.empty():
        restore_tx = globalQ.get().item
        nodeNQ[restore_tx.nodeID].put( TxnWrapper(restore_tx.tick, restore_tx) )
    

'''
# First, create an ordered array of txns in case the original lists are out of (time) order.
txs_in_time_order = []

for i in range(total_txs):
    candidate_tick = hiest_tick
        for k in range( len(txs[j].transactions) ): # for tx in txs[j].transactions:
            tx = txs[j].transactions[k]
            if not txn_ordered[j][k] and tx.tick >= latest_executed_tick and tx.tick <= candidate_tick:
                candidate_tick         = tx.tick
                nxt_txn_node           = j
                nxt_txn_id_within_node = k

    tx_current = txs[nxt_txn_node].transactions[nxt_txn_id_within_node]
    # Just store the order in which txns will be executed.
    txs_in_time_order.append(tx_current)
    latest_executed_tick = tx_current.tick
    txn_ordered[nxt_txn_node][nxt_txn_id_within_node] = 1

print(txs_in_time_order)
'''

executed_txn_cnt = 0
'''
while executed_txn_cnt < total_txs:
   current_txn = txs_in_time_order[executed_txn_cnt]
   if not nodes[current_txn.nodeID].readRequired( int(current_txn.memAddr / cache_line_size_bytes), dir ) and
      not nodes[current_txn.nodeID].fwdRequired ( int(current_txn.memAddr / cache_line_size_bytes), dir ):
      # The node itself has the data. No memory read or fwding happens.
      dataAccess( nodes, current_txn.nodeID, int(tx_current.memAddr / cache_line_size_bytes), dir )
      executed_txn_cnt += 1
   elsif not nodes[current_txn.nodeID].readRequired( int(current_txn.memAddr / cache_line_size_bytes), dir ) and
             nodes[current_txn.nodeID].fwdRequired ( int(current_txn.memAddr / cache_line_size_bytes), dir ):
   elsif nodes[current_txn.nodeID].readRequired( int(current_txn.memAddr / cache_line_size_bytes), dir ):
       # Another node could be reading this, or planning to read it once there's an open port. Needs extra forwarding from other node.
       # Otherwise, this node will try to read it. No fwding needed.
'''

'''
for i in range(total_txs):
    candidate_tick = hiest_tick
    for j in range( len(txs) ):
        for k in range( len(txs[j].transactions) ): # for tx in txs[j].transactions:
            tx = txs[j].transactions[k]

            # No mem read required for this txn AND
            # It is not executed yet AND
            # Its tick is higher than the last executed one's tick (might be redundant from not executed yet) AND
            # Its tick is lower than the current candidate's tick:
            if not nodes[j].readRequired(int(tx.memAddr / cache_line_size_bytes), dir) and not txn_executed[j][k] and tx.tick >= latest_executed_tick and tx.tick <= candidate_tick:
                candidate_tick         = tx.tick
                nxt_txn_node           = j
                nxt_txn_id_within_node = k

            # Mem read required for this txn AND
            # It is not executed yet AND
            # Its tick is higher than the last executed one's tick (might be redundant from not executed yet) AND
            # Its tick is lower than the current candidate's tick:
            elif nodes[j].readRequired(int(tx.memAddr / cache_line_size_bytes), dir) and not txn_executed[j][k] and tx.tick >= latest_executed_tick and tx.    tick <= candidate_tick:
                # If a read is required, check if there is any other txn currently reading the same address,
                # and if not, if there is a free DRAM port.
                found_mem_rd = 0
                for dram_port_idx in range(dram_rd_port_cnt):
                    if dram_port_reading_block[dram_port_idx] == int(tx.memAddr / cache_line_size_bytes):
                        # Another node is bringing in this block, we'll fwd it later.
                        # This txn can execute at {dram_port_started_read[dram_port_idx] + MEMORY_RD + MEMORY_FWD}.
                        found_mem_rd = 1
                        tx_list_to_execute[dram_port_started_read[dram_port_idx] + MEMORY_RD + MEMORY_FWD].append(tx)
                if 0 == found_mem_rd:
                    # Have to find out if there is a free DRAM port, or when will there be one.
                    # Have to find out if there is a free DRAM port, or when will there be one.
                    free_dram = 0
                    for dram_port_idx in range(dram_rd_port_cnt):
                        if -1 == dram_port_reading_block[dram_port_idx]:
                            dram_port_started_read[dram_port_idx]  = tx.tick
                            dram_port_reading_block[dram_port_idx] = int(tx.memAddr / cache_line_size_bytes)
                            free_dram = 1
                    if 0 == free_dram:
                        # Have to save this txn in a queue for DRAM ports becoming available.
                        # TODO Maybe make this a dir{} and save txn along with tick.
                        waiting_for_dram_port.append( txs[nxt_txn_node].transactions[nxt_txn_id_within_node] )
    # Before every new txn, we also have to check DRAM ports for finished mem rds.

    tx_current = txs[nxt_txn_node].transactions[nxt_txn_id_within_node]
    #dataAccess( nodes, tx_current.nodeID, int(tx_current.memAddr / cache_line_size_bytes), dir )
    # Just store the order in which txns will be executed.
    tx_list_to_execute[].append(tx_current)
    latest_executed_tick = tx_current.tick
    txn_executed[nxt_txn_node][nxt_txn_id_within_node] = 1

    print("Time tick (i.e., txn ID):    ", tx_current.tick,
        "\nNode ID:                     ", tx_current.nodeID,
        "\nTxn memory address:          ", tx_current.memAddr,
        "\nTxn block address:           ", int(tx_current.memAddr / cache_line_size_bytes),
        "\nTxn direction:               ", "RD" if tx_current.direction else "WR")
    print("Directory dirty, entries:    ", dir.dirty, dir.entries)
    print("Current txn penalty per node:", tracker, "\n")


'''


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


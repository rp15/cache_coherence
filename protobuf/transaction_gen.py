import transactions_pb2
import sys

# 1) CPU0 RD 0
# 2) CPU1 WR 2
# 3) CPU1 RD 1
# 4) CPU0 RD 1
# 5) CPU1 WR 1 TODO CPU1 already has blkAddr though in 'I' state. This would need to replace that, needs to be implemented in CPU logic.
# 6) CPU2 RD 1

transaction_list0 = transactions_pb2.Transaction_list()
transaction_list1 = transactions_pb2.Transaction_list()
transaction_list2 = transactions_pb2.Transaction_list()

tr1 = transaction_list0.transactions.add()
tr2 = transaction_list1.transactions.add()
tr3 = transaction_list1.transactions.add()
tr4 = transaction_list0.transactions.add()
tr5 = transaction_list1.transactions.add()
tr6 = transaction_list2.transactions.add()

tr1.nodeID = 0
tr1.blkAddr = 0
tr1.direction = 1
tr1.tick = 1

tr2.nodeID = 1
tr2.blkAddr = 2
tr2.direction = 0
tr2.tick = 2

tr3.nodeID = 1
tr3.blkAddr = 1
tr3.direction = 1
tr3.tick = 3

tr4.nodeID = 0
tr4.blkAddr = 1
tr4.direction = 1
tr4.tick = 4

tr5.nodeID = 1
tr5.blkAddr = 1
tr5.direction = 0
tr5.tick = 5

tr6.nodeID = 2
tr6.blkAddr = 1
tr6.direction = 1
tr6.tick = 6

print(tr6)

with open("node0.txt", "wb") as f:
  f.write(transaction_list0.SerializeToString())

with open("node1.txt", "wb") as f:
  f.write(transaction_list1.SerializeToString())

with open("node2.txt", "wb") as f:
  f.write(transaction_list2.SerializeToString())


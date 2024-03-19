import transactions_pb2
import sys

# 0) CPU0 RD 0
# 1) CPU1 WR 2
# 2) CPU1 RD 1
# 3) CPU0 RD 1
# 4) CPU1 WR 1 TODO CPU1 already has memAddr though in 'I' state. This would need to replace that, needs to be implemented in CPU logic.
# 5) CPU2 RD 1

transaction_list0 = transactions_pb2.Transaction_list()
transaction_list1 = transactions_pb2.Transaction_list()
transaction_list2 = transactions_pb2.Transaction_list()

tr0 = transaction_list0.transactions.add()
tr1 = transaction_list1.transactions.add()
tr2 = transaction_list1.transactions.add()
tr3 = transaction_list0.transactions.add()
tr4 = transaction_list1.transactions.add()
tr5 = transaction_list2.transactions.add()

tr0.nodeID = 0
tr0.memAddr = 0
tr0.direction = 1
tr0.tick = 0

tr1.nodeID = 1
tr1.memAddr = 2
tr1.direction = 0
tr1.tick = 1

tr2.nodeID = 1
tr2.memAddr = 1
tr2.direction = 1
tr2.tick = 2

tr3.nodeID = 0
tr3.memAddr = 1
tr3.direction = 1
tr3.tick = 3

tr4.nodeID = 1
tr4.memAddr = 1
tr4.direction = 0
tr4.tick = 4

tr5.nodeID = 2
tr5.memAddr = 1
tr5.direction = 1
tr5.tick = 5

print(tr5)

with open("node0.txt", "wb") as f:
  f.write(transaction_list0.SerializeToString())

with open("node1.txt", "wb") as f:
  f.write(transaction_list1.SerializeToString())

with open("node2.txt", "wb") as f:
  f.write(transaction_list2.SerializeToString())


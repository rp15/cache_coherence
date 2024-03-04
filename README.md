# cache_coherence
To run the directory-based MI protocol, use 
> python3.12 MI/MI.py 3 MI/node0.txt MI/node1.txt MI/node2.txt

To run the directory-based MSI protocol, use 
> python3.12 MSI/MSI.py

To run the directory-based MESI protocol, use
> python3.12 MESI/MESI.py


For MI, the protobuf file can be compiled from the protobuf directory as
> protoc -I=. --python_out=. ./transactions.proto

Then, the transaction .txt file can be created with (still in protobuf/):
> python3.12 transaction_gen.py

(Transactions can be modified/added by changing transaction_gen.py.) 
Finally, the resulting transactions_pb2.py and .txt files need to be copied to MI/.


######################
####### Nodes ########
######################
New nodes can be instantiated by adding more elements to the node array.
The identifier of the node is passed to the constructor.

nodes = []
nodes.append( CPU(0) )
nodes.append( CPU(1) )
nodes.append( CPU(2) )
...

######################
#### Transactions ####
######################
To test new transactions in MI/MSI/MESI, add any number of these to the end of the file:

# 6) CPU2 RD 1: dataAccess(nodes, [CPU node], [memory block address], dir, [RD: 1, WR: 0]).
dataAccess(nodes, 2, 1, dir, 1)
print(dir.dirty, dir.entries)

(Currently, the dirty and present information of the directory is printed after every transaction. The simulations will be enhanced to track total number of cycles and mem write/read transactions to compare performance among different protocols.)


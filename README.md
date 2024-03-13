# cache_coherence
To run the directory-based MI protocol, use 
> python3.12 MI/MI.py 3 MI/node0.txt MI/node1.txt MI/node2.txt

To run the directory-based MSI protocol, use 
> python3.12 MSI/MSI.py 3 MSI/node0.txt MSI/node1.txt MSI/node2.txt

To run the directory-based MESI protocol, use
> python3.12 MESI/MESI.py 3 MESI/node0.txt MESI/node1.txt MESI/node2.txt

To run the scratchpad-based protocol (SP), use
python3.12 SP/SP.py 3 SP/node0.txt SP/node1.txt SP/node2.txt

The protobuf file can be compiled from the protobuf/ directory as
> protoc -I=. --python_out=. ./transactions.proto

Then, the transaction .txt files can be created with (still in protobuf/):
> python3.12 transaction_gen.py

(Transactions can be modified/added by changing transaction_gen.py.) 
Finally, the resulting transactions_pb2.py and .txt files need to be copied to MI/, MSI/, MESI/.


######################
####### Nodes ########
######################
New nodes can be instantiated by changing the first argument of the protocol call (3 in the examples above).

######################
#### Transactions ####
######################
To test new transactions in MI/MSI/MESI/SP, add any number of these to the transaction_gen.py file and rerun the txt generation.

(Currently, the dirty and present information of the directory is printed after every transaction. The simulations will be enhanced to track total number of cycles and mem write/read transactions to compare performance among different protocols.)


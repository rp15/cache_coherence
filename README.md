# cache_coherence
To run the directory-based timed MI protocol, use
> python3.12 MI/MI_timed.py -n 3 -c 1 -r 4 -f 1 -d 1 -i MI/node0.txt -i MI/node1.txt -i MI/node2.txt

To get help with the simulators, run
> python3.12 MI/MI.py -h
> python3.12 MSI/MSI.py -h
> python3.12 MESI/MESI.py -h
> python3.12 SP/SP.py -h

To run the directory-based MI protocol, use 
> python3.12 MI/MI.py -n 3 -c 1 -r 4 -f 1 -i MI/node0.txt -i MI/node1.txt -i MI/node2.txt

To run the directory-based MSI protocol, use 
> python3.12 MSI/MSI.py -n 3 -c 1 -r 4 -f 1 -i MSI/node0.txt -i MSI/node1.txt -i MSI/node2.txt

To run the directory-based MESI protocol, use
> python3.12 MESI/MESI.py -n 3 -c 1 -r 4 -f 1 -i MESI/node0.txt -i MESI/node1.txt -i MESI/node2.txt

To run the scratchpad-based protocol (SP), use
> python3.12 SP/SP.py -n 3 -c 2 -r 300 -f 4 -i SP/node0.txt -i SP/node1.txt -i SP/node2.txt

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

(Currently, the dirty and present information of the directory and total number of penalty cycles per node to compare performance among different protocols are printed after every transaction. The simulations could be enhanced to track mem write/read transactions.)


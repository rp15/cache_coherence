# cache_coherence
To run the directory-based MI protocol, use 
> python3.12 MI/MI.py

To run the directory-based MSI protocol, use 
> python3.12 MSI/MSI.py

To run the directory-based MESI protocol, use
> python3.12 MESI/MESI.py

To test new transactions in MI/MSI/MESI, add any number of these to the end of the file:

# 6) CPU2 RD 1: dataAccess(nodes, [CPU node], [memory block address], dir, [RD: 1, WR: 0]).
dataAccess(nodes, 2, 1, dir, 1)
print(dir.dirty, dir.entries)

(Currently, the dirty and present information of the directory is printed after every transaction. The simulations will be enhanced to track total number of cycles and mem write/read transactions to compare performance among different protocols.)


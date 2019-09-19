# Lamden Mockchain

The mockchain is a special instance of the Lamden blockchain that behaves pretty much identically to the main network deployment, but is contained completely locally. It is designed to 'feel' just like the real blockchain from a developer's standpoint, but has some key differences.

The mockchain is for running a local instance of the Lamden blockchain to develop and test smart contracts or web applications against.

### Key Differences

Here are the things that make the mockchain different:

#### Single Instance
The mockchain is a single instance. It does not connect with other computers or perform consensus. All transactions submitted to the mockchain are processed completely locally, without any risk of packet dropping, network latency, or consensus complications that occur on the real blockchain.

#### One transaction per Block
The mockchain runs on a single computer: your computer. Thus, the need to batch transactions together for efficiency is not required. When you submit a transaction to the mockchain, it is put into its own block and processed immediately. The blockchain component still works, but you'll find that each block just contains a single transaction. The cryptographic nature of the block headers connecting via linked hashes is not affected.

#### Instant Feedback
On a real blockchain, you have an asynchronous waiting period between submitting a transaction, it being processed, and the block being confirmed. On the mockchain, you get a synchronous response on the outcome of your transaction. This is good for testing purposes to understand if your transactions are properly formatted, if your smart contract is misbehaving, etc. It is also perfect for developing test suites against so that you can automatically test functionality against a system that performs pretty much identically to the actual production system. 
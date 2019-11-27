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

## How

### Install Dependencies
branch dependancies are subject to change*

[RocksDb](https://github.com/facebook/rocksdb)

[PyMongo](https://github.com/mongodb/mongo-python-driver)

[Lamden Cilantro Enterprise](https://github.com/Lamden/cilantro-enterprise) *branch rel_electric_egg

[Lamden Contracting](https://github.com/Lamden/contracting)



### Run Servers
Start RockDB and MongoDB servers


### Install Mockchain
```
git clone https://github.com/Lamden/mockchain.git
cd mockchain
```

### Run Server
```
python3 -m mockchain
```
specific port
```
python3 -m mockchain --port <INT> --vk <HEX_STRING>
```

## Usage

Install Lampy and do the following:

```python
In [1]: from lampy import query

In [2]: from lampy import wallet

In [3]: wallet.Wallet()
Out[3]: <lampy.wallet.Wallet at 0x108440828>

In [4]: w = wallet.Wallet()

In [5]: ip = 'http://127.0.0.1:8000'

In [6]: c = query.LamdenClient(ip=ip, wallet=w)

In [7]: c.ping()
Out[7]: {'status': 'online'}

In [8]: c.get_contracts()
Out[8]: ['vkbook', 'currency', 'submission']

```
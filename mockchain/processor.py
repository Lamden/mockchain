from cilantro_ee.protocol.transaction import transaction_is_valid, \
    TransactionNonceInvalid, TransactionProcessorInvalid, TransactionTooManyPendingException, \
    TransactionSenderTooFewStamps, TransactionPOWProofInvalid, TransactionSignatureInvalid, TransactionStampsNegative

from cilantro_ee.storage.state import MetaDataStorage
from cilantro_ee.storage.master import MasterStorage
from cilantro_ee.nodes.delegate.sub_block_builder import UnpackedContractTransaction
from cilantro_ee.messages import capnp as schemas

from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient
from contracting.execution.executor import Executor

from datetime import datetime
import os
import capnp
import hashlib

from . import conf

driver = MetaDataStorage()
blocks = MasterStorage()
client = ContractingClient(executor=Executor(metering=True))

transaction_capnp = capnp.load(os.path.dirname(schemas.__file__) + '/transaction.capnp')


def mint(vk, amount):
    currency = client.get_contract('currency')
    current_balance = currency.quick_read(variable='balances', key=vk) or 0
    currency.quick_write(variable='balances', key=vk, value=amount+current_balance)


def process_transaction(tx: transaction_capnp.Transaction):
    # Deserialize?
    try:
        transaction_is_valid(tx=tx,
                             expected_processor=conf.HOST_VK,
                             driver=driver,
                             strict=True)
    except TransactionNonceInvalid:
        return {'error': 'Transaction nonce is invalid.'}
    except TransactionProcessorInvalid:
        return {'error': 'Transaction processor does not match expected processor.'}
    except TransactionTooManyPendingException:
        return {'error': 'Too many pending transactions currently in the block.'}
    except TransactionSenderTooFewStamps:
        return {'error': 'Transaction sender has too few stamps for this transaction.'}
    except TransactionPOWProofInvalid:
        return {'error': 'Transaction proof of work is invalid.'}
    except TransactionSignatureInvalid:
        return {'error': 'Transaction is not signed by the sender.'}
    except TransactionStampsNegative:
        return {'error': 'Transaction has negative stamps supplied.'}

    # Pass protocol level variables into environment so they are accessible at runtime in smart contracts
    block_hash = driver.latest_block_hash
    block_num = driver.latest_block_num

    dt = datetime.utcfromtimestamp(tx.metadata.timestamp)
    dt_object = Datetime(year=dt.year,
                         month=dt.month,
                         day=dt.day,
                         hour=dt.hour,
                         minute=dt.minute,
                         second=dt.second,
                         microsecond=dt.microsecond)

    environment = {
        'block_hash': block_hash,
        'block_num': block_num,
        'now': dt_object
    }

    transaction = UnpackedContractTransaction(tx)

    status_code, result, stamps_used = client.executor.execute(
        sender=transaction.payload.sender.hex(),
        contract_name=transaction.payload.contractName,
        function_name=transaction.payload.functionName,
        kwargs=transaction.payload.kwargs,
        stamps=transaction.payload.stampsSupplied,
        environment=environment,
        auto_commit=False
    )

    state_changes = client.executor.driver.contract_modifications[0]

    client.executor.driver.commit()

    results = {
        'state_changes': state_changes,
        'status_code': status_code,
        'result': result,
        'stamps_used': stamps_used
    }

    store_block(tx, block_hash, block_num)

    return results


def store_block(tx: transaction_capnp.Transaction, last_hash, last_num):
    b = tx.as_builder().to_bytes_packed()

    h = hashlib.sha3_256()
    h.update(b)

    tx_hash = h.digest()

    i = hashlib.sha3_256()
    i.update(last_hash + tx_hash)

    new_block_hash = i.digest()

    driver.latest_block_hash = new_block_hash
    driver.latest_block_num = last_num + 1

    block = {
        'tx': b,
        'txHash': tx_hash,
        'blockHash': new_block_hash,
        'blockNum': last_num
    }

    blocks.put(block)

from unittest import TestCase
from mockchain import processor
from lampy.wallet import Wallet
from lampy.tx import build_transaction
from cilantro_ee.messages import capnp as schemas
from cilantro_ee.contracts import sync
from mockchain import contracts
import os
import capnp
from contracting.client import ContractingClient
transaction_capnp = capnp.load(os.path.dirname(schemas.__file__) + '/transaction.capnp')


class TestProcessor(TestCase):
    def setUp(self):
        self.wallet = Wallet()
        self.client = ContractingClient()
        sync.sync_genesis_contracts(directory=os.path.dirname(contracts.__file__))
        processor.mint(self.wallet.vk.encode().hex(), 1_000_000_000)

        self.currency = self.client.get_contract('currency')

    def tearDown(self):
        self.client.flush()

    def test_process_good_tx(self):
        tx = build_transaction(wallet=self.wallet,
                               contract='currency',
                               function='transfer',
                               kwargs={'to': 'jeff', 'amount': 10_000},
                               stamps=1_000_000,
                               processor=b'\x00' * 32,
                               nonce=0)

        tx_struct = transaction_capnp.Transaction.from_bytes_packed(tx)

        print(processor.process_transaction(tx_struct))

    def test_mint_works(self):
        sync.sync_genesis_contracts(directory=os.path.dirname(contracts.__file__))
        processor.mint(self.wallet.vk.encode().hex(), 100000)
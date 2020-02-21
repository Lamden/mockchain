from unittest import TestCase
from mockchain import processor

import cilantro_ee
from cilantro_ee.crypto.wallet import Wallet
from cilantro_ee.crypto.transaction import TransactionBuilder
from cilantro_ee.messages.capnp_impl import capnp_struct as capnp_schema
from cilantro_ee.contracts import sync

from mockchain import contracts

import os
import capnp
from contracting.client import ContractingClient
transaction_capnp = capnp.load(os.path.dirname(capnp_schema.__file__) + '/transaction.capnp')

class TestProcessor(TestCase):
    def setUp(self):
        self.wallet = Wallet()
        self.client = ContractingClient()
        sync.submit_from_genesis_json_file(cilantro_ee.contracts.__path__[0] + '/genesis.json', client=ContractingClient())

        processor.mint(self.wallet.vk.encode().hex(), 1000000000)
        self.currency = self.client.get_contract('currency')

        bal = self.currency.quick_read(variable='balances', key=self.wallet.vk.encode().hex())
        self.assertEqual(bal, 1000000000)

    def tearDown(self):
        self.client.flush()

    def test_process_good_tx(self):
        txb = TransactionBuilder(self.wallet.verifying_key(),
                               contract='currency',
                               function='transfer',
                               kwargs={'to': 'jeff', 'amount': 10000},
                               stamps=100000,
                               processor=b'\x00' * 32,
                               nonce=0)

        txb.sign(self.wallet.signing_key())
        tx_bytes = txb.serialize()

        tx = transaction_capnp.NewTransaction.from_bytes_packed(tx_bytes)
        print(tx)

        results = processor.process_transaction(tx)

        balance_from = results['state_changes']['currency.balances:{}'.format(self.wallet.vk.encode().hex())]
        balance_jeff = results['state_changes']['currency.balances:jeff']

        self.assertEqual(float(balance_from), 1000000000 - 10000)
        self.assertEqual(float(balance_jeff), 10000)
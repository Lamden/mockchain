from unittest import TestCase
from mockchain import processor
from lamdenpy.wallet import Wallet
from lamdenpy.tx import build_transaction
from cilantro_ee.core.messages.capnp_impl import capnp_struct as capnp_schema
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
        sync.sync_genesis_contracts(directory=os.path.dirname(contracts.__file__))

        processor.mint(self.wallet.vk.encode().hex(), 1_000_000_000)
        self.currency = self.client.get_contract('currency')

        bal = self.currency.quick_read(variable='balances', key=self.wallet.vk.encode().hex())
        self.assertEqual(bal, 1_000_000_000)

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

        results = processor.process_transaction(tx_struct)
        balance = results['state_changes'].get('currency.balances:{}'.format(self.wallet.vk.encode().hex()))
        balance_jeff = results['state_changes'].get('currency.balances:jeff')

        self.assertEqual(float(balance), 1_000_000_000 - 10_000)
        self.assertEqual(float(balance_jeff), 10_000)

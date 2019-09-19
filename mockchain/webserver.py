from sanic import Sanic
from sanic.response import json
import json as _json
from contracting.client import ContractingClient
from cilantro_ee.storage.master import MasterStorage
from cilantro_ee.storage.state import MetaDataStorage
from cilantro_ee.messages import capnp as schemas

import ast
from . import conf
from . import processor
import os
import capnp

app = Sanic(__name__)
block_driver = MasterStorage()
metadata_driver = MetaDataStorage()
client = ContractingClient()

transaction_capnp = capnp.load(os.path.dirname(schemas.__file__) + '/transaction.capnp')


@app.route("/ping", methods=["GET","OPTIONS",])
async def ping(_):
    return json({'status': 'online'})


@app.route('/id', methods=['GET'])
async def get_id(_):
    return json({'verifying_key': conf.HOST_VK.hex()})


@app.route('/nonce/<vk>', methods=['GET'])
async def get_nonce(_, vk):
    # Might have to change this sucker from hex to bytes.
    pending_nonce = metadata_driver.get_pending_nonce(processor=conf.HOST_VK.hex(), sender=bytes.fromhex(vk))

    if pending_nonce is None:
        nonce = metadata_driver.get_nonce(processor=conf.HOST_VK.hex(), sender=bytes.fromhex(vk))
        if nonce is None:
            pending_nonce = 0
        else:
            pending_nonce = nonce

    return json({'nonce': pending_nonce, 'processor': conf.HOST_VK.hex(), 'sender': vk})


@app.route('/epoch', methods=['GET'])
async def get_epoch(_):
    epoch_hash = metadata_driver.latest_epoch_hash
    block_num = metadata_driver.latest_block_num

    e = (block_num // conf.EPOCH_INTERVAL) + 1
    blocks_until_next_epoch = (e * conf.EPOCH_INTERVAL) - block_num

    return json({'epoch_hash': epoch_hash.hex(),
                 'blocks_until_next_epoch': blocks_until_next_epoch})


@app.route("/", methods=["POST","OPTIONS",])
async def submit_transaction(request):
    try:
        tx_bytes = request.body
        tx = transaction_capnp.Transaction.from_bytes_packed(tx_bytes)

    except Exception as e:
        return json({'error': 'Malformed transaction.'.format(e)}, status=400)

    result = processor.process_transaction(tx)
    return result


# Returns {'contracts': JSON List of strings}
@app.route('/contracts', methods=['GET'])
async def get_contracts(_):
    contracts = client.get_contracts()
    return json({'contracts': contracts})


@app.route('/contracts/<contract>', methods=['GET'])
async def get_contract(_, contract):
    contract_code = client.raw_driver.get_contract(contract)

    if contract_code is None:
        return json({'error': '{} does not exist'.format(contract)}, status=404)
    return json({'name': contract, 'code': contract_code}, status=200)


@app.route("/contracts/<contract>/methods", methods=['GET'])
async def get_methods(_, contract):
    contract_code = client.raw_driver.get_contract(contract)

    if contract_code is None:
        return json({'error': '{} does not exist'.format(contract)}, status=404)

    tree = ast.parse(contract_code)

    function_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    funcs = []
    for definition in function_defs:
        func_name = definition.name
        kwargs = [arg.arg for arg in definition.args.args]

        funcs.append({'name': func_name, 'arguments': kwargs})

    return json({'methods': funcs}, status=200)


@app.route('/contracts/<contract>/<variable>')
async def get_variable(request, contract, variable):
    contract_code = client.raw_driver.get_contract(contract)

    if contract_code is None:
        return json({'error': '{} does not exist'.format(contract)}, status=404)

    key = request.args.get('key')

    k = client.raw_driver.make_key(key=contract, field=variable, args=key)
    response = client.raw_driver.get(k)

    if response is None:
        return json({'value': None}, status=404)
    else:
        return json({'value': response}, status=200)


@app.route("/latest_block", methods=["GET","OPTIONS",])
async def get_latest_block(_):
    index = block_driver.get_last_n(1)
    latest_block_hash = index.get('blockHash')
    return json({'hash': '{}'.format(latest_block_hash) })


@app.route('/blocks', methods=["GET","OPTIONS",])
async def get_block(request):
    if 'number' in request.json:
        num = request.json['number']
        block = block_driver.get_block(num)
        if block is None:
            return json({'error': 'Block at number {} does not exist.'.format(num)}, status=400)
    else:
        _hash = request.json['hash']
        block = block_driver.get_block(_hash)
        if block is None:
            return json({'error': 'Block with hash {} does not exist.'.format(_hash)}, 400)

    return json(_json.dumps(block))


@app.route('/mint', methods=["POST"])
async def mint_currency(request):
    processor.mint(request.json.get('vk'), request.json.get('amount'))
    return json({'success': 'Mint success.'})

def start_webserver(q):
    app.queue = q
    app.run(host='0.0.0.0', port=8000, workers=1, debug=False, access_log=False)

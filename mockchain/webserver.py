from sanic import Sanic
from sanic.response import json

import json as _json

from contracting.client import ContractingClient
from contracting.db.encoder import encode

from cilantro_ee.storage.master import MasterStorage
from cilantro_ee.storage import BlockchainDriver
from cilantro_ee.messages.capnp_impl import capnp_struct as schemas

import ast
from . import conf
from . import processor
import os
import capnp

app = Sanic(__name__)
block_driver = MasterStorage()
metadata_driver = BlockchainDriver()
client = ContractingClient()

#HTTPS
'''
from sanic_cors import CORS, cross_origin
import ssl
SSL_WEB_SERVER_PORT = 443
NUM_WORKERS = 1
ssl_cert = ''
ssl_key = ''
CORS(app, automatic_options=True)
'''

transaction_capnp = capnp.load(os.path.dirname(schemas.__file__) + '/transaction.capnp')


@app.route("/ping", methods=["GET", "OPTIONS"])
async def ping(_):
    return json({'status': 'online'}, status=200)


@app.route('/id', methods=['GET'])
async def get_id(_):
    return json({'verifying_key': conf.HOST_VK.hex()}, status=200)


@app.route('/nonce/<vk>', methods=['GET'])
async def get_nonce(_, vk):
    # Might have to change this sucker from hex to bytes.
    pending_nonce = metadata_driver.get_pending_nonce(processor=conf.HOST_VK, sender=bytes.fromhex(vk))

    if pending_nonce is None:
        nonce = metadata_driver.get_nonce(processor=conf.HOST_VK, sender=bytes.fromhex(vk))
        if nonce is None:
            pending_nonce = 0
        else:
            pending_nonce = nonce

    return json({'nonce': pending_nonce, 'processor': conf.HOST_VK.hex(), 'sender': vk}, status=200)


@app.route("/", methods=["POST","OPTIONS",])
async def submit_transaction(request):
    try:
        tx_bytes = request.body
        tx = transaction_capnp.NewTransaction.from_bytes_packed(tx_bytes)

    except Exception as e:
        return json({'error': 'Malformed transaction.'.format(e)}, status=400)

    result = processor.process_transaction(tx)

    return json(result, status=200)


# Returns {'contracts': JSON List of strings}
@app.route('/contracts', methods=['GET'])
async def get_contracts(_):
    contracts = client.get_contracts()
    return json({'contracts': contracts}, status=200)


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

    if key is None:
        args = []
    else:
        args = [key]

    k = client.raw_driver.make_key(contract, variable, args)
    response = encode(client.raw_driver.get(k))

    if response is None:
        return json({'value': None}, status=404)
    else:
        return json({'value': response}, status=200)


@app.route("/latest_blocks", methods=["GET","OPTIONS",])
async def get_latest_blocks(request):
    num = request.args.get('num')
    if num is None:
        num = 1
    index = block_driver.get_last_n(1)
    return json(index[0], status=200)


@app.route('/blocks', methods=["GET","OPTIONS",])
async def get_block(request):
    num = request.args.get('num')
    if num:
        print(num)
        block = block_driver.get_block(num)
        print (block)
        if block is None:
            return json({'error': 'Block at number {} does not exist.'.format(num)}, status=400)

    _hash = request.args.get('hash')
    if _hash:
        block = block_driver.get_block(_hash)
        if block is None:
            return json({'error': 'Block with hash {} does not exist.'.format(_hash)}, 400)

    return json(block, status=200)


@app.route('/mint', methods=["POST","OPTIONS"])
async def mint_currency(request):
    vk = request.json.get('vk')
    amount = request.json.get('amount')
    processor.mint(request.json.get('vk'), request.json.get('amount'))
    return json({'success': 'Mint success.'}, status=200)


@app.route('/iterate', methods=['GET'])
async def iterate_variable(request, contract, variable):
    contract_code = client.raw_driver.get_contract(contract)

    if contract_code is None:
        return json({'error': '{} does not exist'.format(contract)}, status=404)

    key = request.args.get('key')
    if key is not None:
        key = key.split(',')

    k = client.raw_driver.make_key(key=contract, field=variable, args=key)

    values = client.raw_driver.iter(k, length=500)

    if len(values) == 0:
        return json({'values': None}, status=404)
    return json({'values': values, 'next': values[-1][0]}, status=200)


@app.route('/lint', methods=['POST','OPTIONS'])
async def lint_contract(request):
    code = request.json.get('code')

    if code is None:
        return json({'error': 'no code provided'}, status=200)

    try:
        violations = client.lint(request.json.get('code'))
    except Exception as e:
        violations = e

    return json({'violations': violations}, status=200)


def start_webserver(q):
    app.queue = q

    #HTTP
    app.run(host='0.0.0.0', port=8000, workers=1, debug=False, access_log=False)

    #HTTPS
    '''
    #context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    #context.load_cert_chain(ssl_cert, keyfile=ssl_key)
    #app.run(host='0.0.0.0', port=SSL_WEB_SERVER_PORT, workers=NUM_WORKERS, debug=False, access_log=False, ssl=context)
    '''

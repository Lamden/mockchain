from contracting.client import ContractingClient
from cilantro_ee.contracts import sync
import cilantro_ee

import click
import pyximport
import os

from . import conf

#Set your CONSTITUTION_FILE name in ./conf.py
#Your constitution file should be located in the cilantro-enterprise/constitutions/public/ directory
#of your cilantro-enterprise install.
seed_vkbook(conf.CONSTITUTION_FILE)

from . import webserver
from . import contracts

from multiprocessing import Queue

pyximport.install()


@click.command()
@click.option('--vk')
@click.option('--port')
def boot(vk, port):
    sync.submit_from_genesis_json_file(cilantro_ee.contracts.__path__[0] + '/genesis.json', client=ContractingClient())

    if vk is not None:
        conf.HOST_VK = vk

    if port is not None:
        conf.PORT = int(port)

    if not webserver.app.config.REQUEST_MAX_SIZE:
        webserver.app.config.update({
            'REQUEST_MAX_SIZE': 5,
            'REQUEST_TIMEOUT': 5
        })
    webserver.start_webserver(Queue())


if __name__ == '__main__':
    boot()

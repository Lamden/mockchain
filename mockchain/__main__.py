from cilantro_ee.contracts import sync

import click
import pyximport
import os

from . import conf
from . import webserver
from . import contracts

from multiprocessing import Queue

pyximport.install()


@click.command()
@click.option('--vk')
@click.option('--port')
def boot(vk, port):
    sync.sync_genesis_contracts(directory=os.path.dirname(contracts.__file__))

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

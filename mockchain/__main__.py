import click
import pyximport

from . import conf
from . import webserver

from multiprocessing import Queue

pyximport.install()

@click.command()
@click.option('--vk')
@click.option('--port')
def boot(vk, port):
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

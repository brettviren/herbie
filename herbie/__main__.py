#!/usr/bin/env python3
'''A companion to herbstluftwm.

herbie's architecture follows pub/sub message passing.  Sources of messages
include events from herbstluftwm and filesystem fifo.  Sinks of messages include
herbie components.

'''

import asyncio
from herbie.producers import hcidle
from herbie.consumers import chirp
from herbie.pubsubhub import Hub

import click
@click.group()
@click.pass_context
def cli(ctx):
    pass

@cli.command()
@click.pass_context
def version(ctx):
    'Print the version.'
    print(herbie.__version__)


@cli.command()
@click.pass_context
def daemon(ctx):
    '''
    Start herbie in daemon mode.
    '''
    loop = asyncio.get_event_loop()
    hub = Hub()
    ers = [hcidle(hub), chirp(hub)]
    loop.run_until_complete(asyncio.gather(*ers))

@cli.command()
@click.pass_context
def client(ctx):
    '''
    Send a herbie daemon a message.
    '''



def main():
    cli(obj={})


if '__main__' == __name__:
    main()

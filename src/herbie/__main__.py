#!/usr/bin/env python3
'''A companion to herbstluftwm.
'''
import click
import asyncio
from herbie.aherbie import Herbie
import logging
log = logging.getLogger("herbie")


def set_logging(log_level="DEBUG", log_file=None):
    log.setLevel(log_level)
    fmt = logging.Formatter('%(asctime)s - %(name)s - '
                            '%(levelname)s - %(message)s')
    if log_file is None:
        hand = logging.StreamHandler()
    else:
        hand = logging.FileHandler(log_file)
    hand.setLevel(log_level)
    hand.setFormatter(fmt)
    log.addHandler(hand)


@click.group()
@click.option("-h", "--hc", default="herbstclient",
              help="Set the herbstclient executable name")
@click.option("-c", "--config",
              type=click.Path(),
              help="Set configuration file")
@click.option("-l", "--log-file", default=None,  # fixme, use XDG
              help="Set log file, default is terminal")
@click.option("-L", "--log-level", default="INFO",
              help="Set log level")
@click.pass_context
def cli(ctx, hc, log_file, log_level, config):
    import herbie.astluft
    herbie.astluft.herbstclient = hc
    set_logging(log_level.upper(), log_file)
    ctx.obj = Herbie(config)


@cli.command("version")
def version():
    '''
    Print the version
    '''
    import herbie
    print(herbie.__version__)

@cli.command("hooks")
@click.pass_context
def hooks(ctx):
    '''
    Start herbie loop and respond react to herbstlufwm hooks
    '''
    asyncio.run(ctx.obj.run())


def main():
    cli(obj=None)


if '__main__' == __name__:
    main()

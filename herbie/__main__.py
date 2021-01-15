#!/usr/bin/env python3
'''Someday a true rain will come and wash out a real Python interface
to herbstluftwm.  Until then, there is this.
'''

from herbie.util import toscreen

import click
@click.group()
def cli():
    pass

@cli.command("task")
@click.argument("name")
def task(name):
    '''
    Fill screen with task layout
    '''
    # fixme: move to some real config system
    import herbie.tasks
    meth = getattr(herbie.tasks, name)
    tree = meth()
    toscreen(name, tree)
    pass

def main():
    cli(obj=None)


if '__main__' == __name__:
    main()

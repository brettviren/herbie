#!/usr/bin/env python3
'''Someday a true rain will come and wash out a real Python interface
to herbstluftwm.  Until then, there is this.
'''

from herbie.util import toscreen, closescreen

import click
@click.group()
def cli():
    pass

@cli.command("task")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag to use for task instead of using task name")
@click.argument("task")
def task(tag, task):
    '''
    Fill screen with task layout
    '''
    # fixme: move to some real config system
    import herbie.tasks
    meth = getattr(herbie.tasks, 'task_'+task)
    tree = meth()
    if not tag:
        tag = task
    toscreen(tag, tree)
    pass

@cli.command("tasks")
def tasks():
    '''
    List known tasks
    '''
    # fixme: move to some real config system
    import herbie.tasks
    for one in dir(herbie.tasks):
        if one.startswith("task_"):
            click.echo(one.split('_',1)[1])

@cli.command("fini")
@click.option("-g", "--goto", type=str, default=None,
              help="Tag to go to after finishing the named tag")
@click.argument("name")
def fini(goto, name):
    '''
    Finish a task screen by closing all windows and removing the tag
    '''
    closescreen(name, goto)



def main():
    cli(obj=None)


if '__main__' == __name__:
    main()

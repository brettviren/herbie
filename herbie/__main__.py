#!/usr/bin/env python3
'''Someday a true rain will come and wash out a real Python interface
to herbstluftwm.  Until then, there is this.
'''

from herbie.util import toscreen, closescreen, current_tags

import click
@click.group()
@click.option("-u","--ui",
              default="term",
              type=click.Choice(["term","dmenu","gui"]), 
              help="Set user interface")
@click.pass_context
def cli(ctx, ui):
    import importlib
    uimod = importlib.import_module("herbie."+ui)
    ctx.obj["ui"] = uimod

@cli.command()
@click.pass_context
def version(ctx):
    'Print the version'
    import herbie
    ctx.obj["ui"].echo(herbie.__version__)

@cli.command("tags")
@click.option("-o","--order", default="index",
              type=click.Choice(["index","name"]),
              help="Set ordering")
def tags(order):
    '''
    Print tags one line at a time in order
    '''
    tags = current_tags(order)
    click.echo('\n'.join(tags))

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
@click.pass_context
def tasks(ctx):
    '''
    List known tasks
    '''
    # fixme: move to some real config system
    import herbie.tasks
    lines = list()
    for one in dir(herbie.tasks):
        if one.startswith("task_"):
            lines.append(one.split('_',1)[1])
    ctx.obj['ui'].echo(lines)

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
    cli(obj={})


if '__main__' == __name__:
    main()

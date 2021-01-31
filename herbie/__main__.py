#!/usr/bin/env python3
'''Someday a true rain will come and wash out a real Python interface
to herbstluftwm.  Until then, there is this.
'''
import herbie

from herbie.stluft import WM

from herbie.util import (
    toscreen, closescreen, 
    select_window,
    available, get_task)

import click
@click.group()
@click.option("-h","--hc",default="herbstclient",
              help="Set the herbstclient executable name")
@click.option("-u","--ui",
              default="term",
              type=click.Choice(["term","dmenu","gui"]), 
              help="Set user interface")
@click.pass_context
def cli(ctx, hc, ui):
    import importlib
    uimod = importlib.import_module("herbie."+ui)
    ctx.obj["ui"] = uimod
    ctx.obj["wm"] = WM(hc)

@cli.command()
@click.pass_context
def version(ctx):
    'Print the version'
    ctx.obj["ui"].echo(herbie.__version__)

@cli.command("wselect")
@click.pass_context
def wselect(ctx):
    'Select and focus a window'

    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    got = select_window(wm, ui)
    if got:
        wm(f'jumpto {got}')

@cli.command("wbring")
@click.pass_context
def wbring(ctx):
    'Bring and focus a window on current tab'
    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    got = select_window(wm, ui, "other")
    if got:
        wm(f'bring {got}')

@cli.command("tags")
@click.option("-o","--order", default="index",
              type=click.Choice(["index","name"]),
              help="Set ordering")
@click.pass_context
def tags(ctx, order):
    '''
    Print tags one line at a time in order
    '''
    tags = ctx.obj['wm'].current_tags(order)
    ctx.obj['ui'].echo('\n'.join(tags))

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

@cli.command("itask")
@click.pass_context
def itask(ctx):
    '''
    Interactively figure how to fill screen with task layout
    '''
    wm = ctx.obj['wm']
    tasks = available("task")
    got = ctx.obj['ui'].choose(tasks, "Task: ")
    if not got:
        return
    got = got.split()
    tag = task = got[0]
    if len(got) > 1:
        tag = got[1]
        
    tree = get_task(task)
    toscreen(wm, tag, tree)



@cli.command("tasks")
@click.pass_context
def tasks(ctx):
    '''
    List known tasks
    '''
    # fixme: move to some real config system
    ctx.obj['ui'].echo(available("task"))

@cli.command("fini")
@click.option("-g", "--goto", type=str, default=None,
              help="Tag to go to after finishing the named tag")
@click.argument("name")
def fini(goto, name):
    '''
    Finish a task screen by closing all windows and removing the tag
    '''
    closescreen(name, goto)

@cli.command("ifini")
@click.pass_context
def ifini(ctx):
    '''
    Interactively finish a task screen by closing all windows and removing the tag
    '''
    wm = ctx.obj['wm']
    tags = wm.current_tags()
    got = ctx.obj['ui'].choose(tags, "Tag to finish: ")
    if not got:
        return
    got = got.split()
    name = got[0]
    goto = None
    if len(got) > 1:
        goto = got[1]
    closescreen(wm, name, goto)


@cli.command("loop")
@click.argument("looper")
@click.pass_context
def loop(ctx, looper):
    '''
    Run a looper
    '''
    wm = ctx.obj['wm']
    import herbie.loops
    meth = getattr(herbie.loops, 'loop_'+looper)
    meth(wm)
    
@cli.command("loops")
@click.pass_context
def loops(ctx):
    '''
    List known loopers
    '''
    ctx.obj['ui'].echo(available("loop"))

    

# @cli.command("switch")
# @click.pass_context
# def switch(ctx):
#     '''
#     Switch windows.
#     '''
#     wm = ctx.obj['wm']
#     switch_windows(wm)



def main():
    cli(obj={})


if '__main__' == __name__:
    main()

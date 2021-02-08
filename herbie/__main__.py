#!/usr/bin/env python3
'''Someday a true rain will come and wash out a real Python interface
to herbstluftwm.  Until then, there is this.
'''
import sys
import herbie

from herbie.stluft import WM

from herbie.util import (
    toscreen, closescreen, 
    select_window, make_tree,
    available, get_task)

import click
@click.group()
@click.option("-h","--hc",default="herbstclient",
              help="Set the herbstclient executable name")
@click.option("-u","--ui",
              default="gui",
              type=click.Choice(["term", "gui"]), 
              help="Set user interface")
@click.pass_context
def cli(ctx, hc, ui):
    import importlib
    uimod = importlib.import_module("herbie."+ui)
    ctx.obj["ui"] = uimod.UI()
    ctx.obj["wm"] = WM(hc)

@cli.command()
@click.pass_context
def version(ctx):
    'Print the version'
    ctx.obj["ui"].echo(herbie.__version__)

@cli.command("wselect")
@click.option("-t", "--tags", type=str, default=None,
              help="Which tags to consider, focus=None or all or other")
@click.pass_context
def wselect(ctx, tags):
    'Select and focus a window'

    if tags is None or tags == "focus":
        tags = None
    elif tags in ["all","other"]:
        tags = tags
    else:
        tags = tags.split(",")

    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    ui.monitor = "focused"
    ui.width = -50

    got = select_window(wm, ui, tags)
    if got:
        wm(f'jumpto {got}')

@cli.command("wbring")
@click.pass_context
def wbring(ctx):
    'Bring and focus a window on current tab'
    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    ui.monitor = "focused"
    ui.width = -50
    got = select_window(wm, ui, "other")
    if got:
        wm(f'bring {got}')

@cli.command("waction")
@click.pass_context
def waction(ctx):
    '''
    Select and perform an action on a window
    '''
    wm = ctx.obj['wm']
    cmdlist = [
        ("Close", "close"),
        ("Toggle fullscreen", "fullscreen toggle"),
        ("Toggle pseudotile", "pseudotile toggle"),
    ]
    for tag in wm.current_tags():
        cmdlist.append((f'Move to tag {tag}', f'move {tag}'))
    ui = ctx.obj['ui']
    ui.monitor = "focused_window"
    ui.location = 'tl'
    ui.lines = len(cmdlist)
    got = ui.choose([c[0] for c in cmdlist], "Window action")
    if not got:
        return
    got = got.strip()
    for arg, cmd in cmdlist:
        if arg != got:
            continue
        wm(cmd)
        return


@cli.command("layout")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag or current tag")
@click.option("-a", "--action", default="save",
              type=click.Choice(["load","save","drop"]),
              help="Operation to perform")
@click.argument("args", nargs=-1)
@click.pass_context
def do_layout(ctx, tag, action, args):
    '''
    Command to operate on layouts from a rofi script.
    action in {load, save, drop}
    '''
    wm = ctx.obj['wm']
    tag = tag or wm.focused_tag

    sys.stderr.write(f'{tag} {action} {args}\n')

    NUL = '\0'
    GS = '\x1d'                    # ascii group separator
    RS = '\x1e'                    # ascii record separator
    US = '\x1f'                    # ascii unit separator
    NL = '\n'

    sys.stdout.write(f'{NUL}message{US}<b>{action.capitalize()}</b> layouts for <b>{tag}</b> tag{NL}')
    sys.stdout.write(f'{NUL}markup-rows{US}true{NL}')
    sys.stdout.write(f'{NUL}prompt{US}layout to {action}{NL}')

    cursexp = wm(f'dump {tag}').strip()
    oldlays = herbie.layouts.read_store(wm, tag)
    choices, lays = herbie.layouts.rofi(wm, tag, oldlays, cursexp)

    meths = {
        "save": lambda lay : herbie.layouts.add_store(wm, lay, tag),
        "drop": lambda lay : herbie.layouts.del_store(wm, lay, tag),
        "load": lambda lay : wm(f'load {tag} "{lay.sexp}"'),
    }
    meth = meths[action]

    if args:                    # got selection
        for arg in args:
            try:
                lay = lays[arg]
            except KeyError:
                lay = herbie.layouts.Layout(arg, cursexp)
            meth(lay)
        return

    # if no args, print rofi items
    for choice in choices:
        print(choice)


@cli.command("load")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag of layout to save, def is current tag")
@click.pass_context
def load(ctx, tag):
    '''
    Load a saved layout of the tag.
    '''
    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    tag = tag or wm.focused_tag

    cursexp = wm(f'dump {tag}').strip()
    oldlays = herbie.layouts.read_store(wm, tag)
    choices = herbie.layouts.rofi(wm, tag, oldlays, cursexp)

    ui.width = -50
    ui.retform = 'i'            # index
    got = ui.choose(choices, "Load layout",
                    "Pick layout to load")
    if got is None:
        return
    try:
        got = int(got)
    except ValueError:
        return
    lay = oldlays[got]
    wm(f'load {tag} "{lay.sexp}"')

@cli.command("save")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag of layout to save, def is current tag")
@click.option("-p", "--purge", is_flag=True, default=False,
              help="Purge prior saves before adding the current layout")
@click.pass_context
def save(ctx, tag, purge):
    '''
    Add the current layout to those saved on the tag.
    '''
    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    tag = tag or wm.focused_tag

    if purge:
        herbie.layouts.purge(wm, tag)

    cursexp = wm(f'dump {tag}').strip()
    oldlays = herbie.layouts.read_store(wm, tag)
    choices = herbie.layouts.rofi(wm, tag, oldlays, cursexp)

    ui.width = -50
    got = ui.choose(choices, "Save layout to",
                    "Give a new name or overwrite existing")
    if not got:
        return
    got = got.strip().split()[0]
    herbie.layouts.add_store(wm, herbie.layouts.Layout(got, cursexp), tag)



@cli.command("svgdump")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag of layout to dump, def is current tag")
@click.option("-o", "--output", type=str, default=None,
              help="Output svg file name")
@click.pass_context
def svgdump(ctx, tag, output):

    wm = ctx.obj['wm']
    tag = tag or wm.focused_tag
    tree = make_tree(wm(f'dump {tag}'))
    # fixme: auto determine width/height
    herbie.svg.make_icon(output, tree)


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
    ui = ctx.obj['ui']
    ui.monitor = "focused"
    ui.width = -20
    ui.lines = len(tasks)
    got = ui.choose(tasks, "Task")
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

#!/usr/bin/env python3
'''Someday a true rain will come and wash out a real Python interface
to herbstluftwm.  Until then, there is this.
'''
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

@cli.command("load")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag of layout to save, def is current tag")
@click.pass_context
def save(ctx, tag):
    '''
    Load a saved layout of the tag.
    '''
    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    tag = tag or wm.focused_tag

    try:
        stored = wm(f'attr tags.by-name.{tag}.my_layouts')
    except RuntimeError:
        return
    stored = stored.split('\n')
    curtree = wm(f'dump {tag}').strip()
    choices = list()
    byname = dict()
    for lay in stored:
        if not lay:
            continue
        name, tree = lay.split(':', 1)
        byname[name] = tree
        if tree == curtree:
            name += f'\tsame:{tree}' 
        else:
            name += f'\tdiff:{tree}'
        choices.append(name)
    got = ui.choose(choices, "Load name")
    if not got:
        return
    got = got.strip().split()[0]
    totree = byname[got]
    wm(f'load {tag} "{totree}"')

def svg_line(x1, y1, x2, y2):
    return f"<line stroke='gray' stroke-width='1px' x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' />"

def svg_tree(tree, x, y, w, h):
    ratio = getattr(tree, "ratio", None)
    if ratio is None:
        print("svg_tree:", tree)
        return []

    if tree.orient == "horizontal":
        lx = x + w * ratio
        lines = [svg_line(lx, y, lx, y+h)]
        childs = tree.children
        if not childs:
            return lines
        print("horizontal:", tree, "with", len(childs))
        lines += svg_tree(childs[0],  x, y, w*ratio, h)
        lines += svg_tree(childs[1], lx, y, w*(1.0-ratio), h)
        return lines

    # vertical
    ly = y + h * ratio
    lines = [svg_line(x, ly, x+w, ly)]
    childs = tree.children
    print("vertical:", tree, "with", len(childs))
    if not childs:
        return lines
    lines += svg_tree(childs[0], x, y, w, h*ratio) 
    lines += svg_tree(childs[1], x, ly, w, h*(1-ratio))
    return lines
        


@cli.command("svgdump")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag of layout to dump, def is current tag")
@click.option("-o", "--output", type=str, default=None,
              help="Output svg file name")
@click.pass_context
def svgdump(ctx, tag, output):
    wm = ctx.obj['wm']
    tag = tag or wm.focused_tag
    # todo get from x11
    width, height = (384,216)
    lines = [f"<svg width='{width}px' height='{height}px' xmlns='http://www.w3.org/2000/svg' version='1.1' xmlns:xlink='http://www.w3.org/1999/xlink'>"]
    tree = make_tree(wm(f'dump {tag}'))
    lines += svg_tree(tree, 0, 0, width, height)
    lines += ["</svg>"]
    text = '\n'.join(lines)
    if output:
        open(output, 'wb').write(text.encode())
    else:
        print(text)

@cli.command("save")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag of layout to save, def is current tag")
@click.option("-p", "--purge", is_flag=True, default=False,
              help="Purge any saved layouts")
@click.pass_context
def save(ctx, tag, purge):
    '''
    Save the layout of the tag.
    '''
    wm = ctx.obj['wm']
    ui = ctx.obj['ui']
    tag = tag or wm.focused_tag

    try:
        wm(f'new_attr string tags.by-name.{tag}.my_layouts')
    except RuntimeError:
        pass            # assume alread set

    if purge:
        wm(f'set_attr tags.by-name.{tag}.my_layouts ""')

    # layouts are stored as \n-delim lines of ASCII units.  Each
    # layout has a name followed by a colon and the rest is the layout
    # tree as from hc dump.
    stored = wm(f'attr tags.by-name.{tag}.my_layouts').split('\n')
    print('STORED:',stored)
    curtree = wm(f'dump {tag}').strip()
    byname = dict()
    choices = list()
    for lay in stored:
        if not lay:
            continue
        print(f'xxx{lay}xxx')
        name, tree = lay.split(':', 1)
        byname[name] = tree
        if tree == curtree:
            name += f'\tsame:{tree}' 
        else:
            name += f'\tdiff:{tree}'
        choices.append(name)

    got = ui.choose(choices, "Save name",
                    "Give a new name or overwrite existing")
    if not got:
        return
    got = got.strip().split()[0]
    byname[got] = curtree
    tosave = [k+':'+v for k,v in sorted(byname.items())]
    text = '\n'.join(tosave)
    print(f'saving:\n{text}')
    wm(f'set_attr tags.by-name.{tag}.my_layouts "{text}"')
    


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

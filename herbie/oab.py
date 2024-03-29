#!/usr/bin/env python3
'''Someday a true rain will come and wash out a real Python interface
to herbstluftwm.  Until then, there is this.
'''
import os
import sys
import configparser
import herbie
import herbie.tasks
from herbie import rofi
from herbie.stluft import WM
from herbie.util import (
    closescreen, 
    select_window, make_tree,
    available)

import click
@click.group()
@click.option("-h","--hc",default="herbstclient",
              help="Set the herbstclient executable name")
@click.option("-u","--ui",
              default="gui",
              type=click.Choice(["term", "gui"]), 
              help="Set user interface")
@click.option("-c","--config",
              default=[os.environ["HOME"]+"/.herbierc"],
              envvar='HERBIERC',
              multiple=True,
              type=click.Path(),
              help="Set configuration file")
@click.pass_context
def cli(ctx, hc, ui, config):
    import importlib
    uimod = importlib.import_module("herbie."+ui)
    ctx.obj["ui"] = uimod.UI()
    ctx.obj["wm"] = WM(hc)
    cfg = configparser.ConfigParser()
    cfg.read(config)
    ctx.obj["cfg"] = cfg 

@cli.command()
@click.pass_context
def version(ctx):
    'Print the version.'
    ctx.obj["ui"].echo(herbie.__version__)

@cli.command("wselect")
@click.option("-t", "--tags",
              type=click.Choice(["focus","all","other"]),
              default="focus",
              help="Which tags to consider")
@click.argument("args", nargs=-1)
@click.pass_context
def wselect(ctx, tags, args):
    '''
    Select a window for focus.
    '''
    wm = ctx.obj['wm']
    m = rofi.window_cmd_menu(wm, tags,
                             "Select window", "jumpto {winid}")
    rofi.menu.run(m, rofi_version="1.6", debug=False)


@cli.command("wbring")
@click.option("-t", "--tags", 
              type=click.Choice(["focus","all","other"]),
              default="other",
              help="Which tags to consider")
@click.argument("args", nargs=-1)
@click.pass_context
def wbring(ctx, tags, args):
    '''
    Bring a window to a tag.
    '''
    wm = ctx.obj['wm']
    m = rofi.window_cmd_menu(wm, tags,
                             "Bring window", "bring {winid}")
    rofi.menu.run(m, rofi_version="1.6", debug=False)
    

@cli.command("waction")
@click.pass_context
def waction(ctx):
    '''
    Select and perform an action on a window.
    '''
    wm = ctx.obj['wm']
    cmdlist = [
        ("Minimize", "set_attr clients.focus.minimized true"),
        ("Close", "close"),
        ("Toggle fullscreen", "fullscreen toggle"),
        ("Toggle pseudotile", "pseudotile toggle"),
        ("Toggle floating", "pseudotile floating"),
    ]
    for tag in wm.current_tags('my_focus_time'):
        cmdlist.append((f'Move to tag {tag}',
                        f'move {tag};use {tag}'))
    ui = ctx.obj['ui']
    ui.monitor = "focused_window"
    ui.location = 'tl'
    ui.lines = len(cmdlist)
    got = ui.choose([c[0] for c in cmdlist], "Window action")
    #print(f'got: {got}')
    if not got:
        return
    got = got.strip()
    for arg, cmd in cmdlist:
        if arg != got:
            continue
        if ";" in cmd:
            for one in cmd.split(";"):
                one = one.strip()
                if not one:
                    continue
                wm.add(one)
            wm.run()
            return
        
        # immediate
        wm(cmd)
        return
    
    
    # Note, may need Ctrl-Enter to avoid picking match
    if " " in got:              # treat as command(s)
        print(f'got: {got}')
        for one in got.split(";"):
            one = one.strip()
            if not one:
                continue
            wm.add(one)
        wm.run()
        return

    # else treat as name of new tag
    wm.add(f'add {got}')
    wm.add(f'move {got}')
    wm.add(f'use {got}')
    wm.run()

@cli.command("hc")
@click.argument("args", nargs=-1)
@click.pass_context
def hc(ctx, args):
    '''
    Pass-through to herbstclient.
    '''
    wm = ctx.obj['wm']
    res = wm(list(args))
    print(res)



@cli.command("wswap")
@click.option("-d","--direction",
              type=click.Choice(["left","right","above","below"]),
              help="Specify the direction in which to find a neighbor")
@click.option("-w","--windows", nargs=2,
              help="Give two window IDs to swap")
@click.pass_context
def wswap(ctx, direction, windows):
    '''
    Swap focused window with neighbor in given direction.
    '''
    #print (windows)
    wm = ctx.obj['wm']
    if windows:
        layout = wm("dump")
        tag = wm.focused_tag
        # print (layout)
        # move one out of way
        layout = layout.replace(windows[0], "TMP")
        layout = layout.replace(windows[1], windows[0])
        layout = layout.replace("TMP", windows[1])
        #print(layout)
        wm(f"load {tag} '{layout}'")

    else:
        cmd=f"substitute OLDWIN clients.focus.winid chain , focus {direction} , substitute NEWWIN clients.focus.winid spawn herbie wswap --windows OLDWIN NEWWIN"
        #print(cmd)
        wm(cmd)



    
@cli.command("layouts")
@click.option("-l", "--load", type=str, default=None,
              help="Name the layout to load")
@click.pass_context
def do_layouts(ctx, load):
    from .layouts import read_store
    wm = ctx.obj['wm']

    if load:
        for one in read_store(wm):
            if one.name == load:
                cmd=one.sexp
                #print(cmd)
                wm(f'load "{cmd}"')
                return
    # for one in read_store(wm):
    #     print (one)

    

@cli.command("layout")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag or current tag")
@click.option("-a", "--action",
              type=click.Choice(["load","save","drop","all"]),
              default="all",
              help="Name layout action")
@click.argument("args", nargs=-1)
@click.pass_context
def do_layout(ctx, tag, action, args):
    '''
    A rofi modi for loading, saving, dropping layouts.

    Example commands:

    rofi -modi "l:herbie layout -a load" -show l

    rofi -modi "s:herbie layout -a save" -show s

    rofi -modi "d:herbie layout -a drop" -show d

    rofi -modi "a:herbie layout -a all" -show a 
    '''
    # hide our args except prgram name from rofi_menu
    sys.argv[1:] = args
    wm = ctx.obj['wm']
    tag = tag or wm.focused_tag
    lm = rofi.layout_menu(wm, action, tag)
    # sys.stderr.write(str(lm) + "\n")
    rofi.menu.run(lm, rofi_version="1.6", debug=False)
    



@cli.command("svgicon")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag of layout to dump, def is current tag")
@click.option("-n", "--name", type=str, default=None,
              help="Icon name, no extension")
@click.option("-W", "--width", type=int, default=100,
              help="Icon width in pixels")
@click.option("-H", "--height", type=int, default=100,
              help="Icon height in pixels")
@click.pass_context
def svgicon(ctx, tag, name, width, height):
    '''
    Render a tag as an SVG.
    '''

    wm = ctx.obj['wm']
    tag = tag or wm.focused_tag
    tree = make_tree(wm(f'dump {tag}'))
    # fixme: auto determine width/height
    if name is None:
        name = f'herbie-{tag}-{width}x{height}'
    fname = herbie.svg.make_icon(name, tree, width, height)
    print(fname)


@cli.command("totag")
@click.argument("tag")
@click.pass_context
def totag(ctx, tag):
    '''Make tag active or if already then use previously active tag.

    The tag is assumed to be an index into the tag list if its an
    integer, else it's assumed to be a tag.
    '''
    wm = ctx.obj['wm']
    tags = wm.current_tags()
    try:
        ind = int(tag)
        nam = tags[ind]
    except ValueError:
        ind = tags.index(tag)
        nam = tag
    if nam == wm.focused_tag:
        wm("use_previous")
    else:
        wm(f'use_index {ind}')

@cli.command("tags")
@click.option("-o","--order", default="index",
              type=str,
              help="Set ordering")
@click.pass_context
def tags(ctx, order):
    '''
    Print tags one line at a time in order.
    '''
    tags = ctx.obj['wm'].current_tags(order)
    ctx.obj['ui'].echo('\n'.join(tags))


@cli.command("task")
@click.option("-t", "--tag", type=str, default=None,
              help="Name the tag to use for task instead of using task name")
@click.argument("task")
@click.pass_context
def task(ctx, tag, task):
    '''
    Produce a predefined task layout.
    '''
    herbie.tasks.toscreen(ctx.obj['wm'], ctx.obj['cfg'], task, tag)


@cli.command("tasks")
@click.pass_context
def tasks(ctx):
    '''
    List tasks available in the configuration.
    '''
    cfg = ctx.obj['cfg']
    lines = herbie.tasks.available(cfg)
    ctx.obj['ui'].echo(lines, "herbie tasks")


@cli.command("itask")
@click.pass_context
def itask(ctx):
    '''
    Interactively figure how to fill screen with task layout.
    '''
    wm = ctx.obj['wm']
    cfg = ctx.obj['cfg']
    tasks = herbie.tasks.available(cfg)
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
        
    herbie.tasks.toscreen(wm, cfg, task, tag)


@cli.command("fini")
@click.option("-g", "--goto", type=str, default=None,
              help="Tag to go to after finishing the named tag")
@click.argument("name")
def fini(goto, name):
    '''
    Finish a task screen by closing all windows and removing the tag.
    '''
    closescreen(name, goto)
    

@cli.command("ifini")
@click.pass_context
def ifini(ctx):
    '''
    Interactively finish a task screen by closing all windows and removing the tag.
    '''
    wm = ctx.obj['wm']
    #sys.stderr.write('ifini\n')
    tags = wm.current_tags('my_focus_time')
    tags.reverse()
    #sys.stderr.write(str(tags) + '\n')
    ui = ctx.obj['ui']
    ui.monitor = "focused"
    ui.width = -20
    ui.lines = len(tags)
    got = ui.choose(tags, "Tag to finish: ")
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
    Run a looper.
    '''
    wm = ctx.obj['wm']
    import herbie.loops
    meth = getattr(herbie.loops, 'loop_'+looper)
    meth(wm)

    
@cli.command("loops")
@click.pass_context
def loops(ctx):
    '''
    List known loopers.
    '''
    ctx.obj['ui'].echo(available("loop"))

    

def main():
    cli(obj={})


if '__main__' == __name__:
    main()

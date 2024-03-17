#!/usr/bin/env python3
'''herbie tasks are provides in the configuration file section

    [tasks]
    task1 = (...)
    task2 = (...)

The value of a task is a sexp expression such as produced by "hc dump"
but with an extra attribute allowed anywhere you might otherwise see
window IDs ("0x....").  The window attributes name other sections like:

    [window AAA]
    command = program -opt AAA
    class = TheAppClass
    instance = theapp
    title = The X11 Window Title
    
    [window BBB]
    command = program -opt BBB
    class = TheAppClass
    instance = theapp
    title = The X11 Window Title

To make a task with one split and each half with one of these two
instances:

    [tasks]
    aaabbb = (split horizontal:0.50:1 
                    (clients window:AAA)
                    (clients window:BBB))

Consider binding like:

    hc keybind $Mod-i       spawn herbie itask 
    hc keybind $Mod-Shift-i spawn herbie ifini

'''


from herbie.util import make_tree, render_split

def available(cfg):
    lines = list()
    for t in cfg['tasks']:
        lines.append(t)
    return lines

def windows_config(cfg):
    ret = dict()
    for sec in cfg:
        if not sec.startswith("window "):
            continue
        _, name = sec.split(' ', 1)

        secd = dict()
        for k in cfg[sec]:
            secd[k] = cfg[sec][k]
        ret[name] = secd
    return ret

from anytree import Node
from anytree.resolver import Resolver, ChildResolverError

def toscreen(wm, cfg, task, tag = None):
    tag = tag or task

    try:
        wm.taginfo(tag)
    except KeyError:
        wm(f'add {tag}')

    wincfg = windows_config(cfg)

    try:
        dump = cfg["tasks"][task]
    except KeyError:
        print(f'no task {task}, will just make a tag')
        wm.add(f'use {tag}')
        wm.run()
        return

    tree = make_tree(dump)

    layout = render_split(tree)
    print("Layout:",layout)
    if layout:
        wm(f'load {tag} "{layout}"')

    text = wm(f'dump {tag}')
    have = make_tree(text)

    r = Resolver()
    for node in [tree] + list(tree.descendants):
        print(node)
        if not hasattr(node, 'windows'):
            print(f'no windows in {node}')
            continue
        pathlist = [str(n.name) for n in node.path]
        path = '/'.join(pathlist)
        path = '/' + path
        try:
            got = r.get(have, path)
            got = getattr(got, "wids", None)
        except ChildResolverError:
            got = None
        if got:
            print(f'no got for {node}')
            continue
        for window in node.windows:
            wc = wincfg[window]
            command = wc.pop("command", None)
            if command is None:
                continue
            match = ' '.join(['%s="%s"'%(k,v) for k,v in wc.items()])
            index = ''.join(pathlist[1:])
            print(f'index:{index} match:{match}')
            wm.add(f'rule once {match} tag={tag} index={index} maxage=10')
            wm.add(f'spawn {command}')
    
    wm.add("focus_monitor 0")
    wm.add(f'use {tag}')
    wm.run()
    

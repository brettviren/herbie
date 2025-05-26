#!/usr/bin/env python
'''
herbie support for layouts

This module holds ways to process information such given by "hc dump".

herbie stores layout data on a per tag basis in files under
   ~/.config/herbie/layouts/<tag>/<name>
'''

import os
import sys
from herbie.util import make_tree
from herbie.svg import make_icon
from collections import namedtuple
from pathlib import Path

# in herbie we use this object representation for all info about a
# "layout"
Layout = namedtuple("Layout", "name sexp")


base_path = Path.home() / ".config/herbie/layouts"

def tag_path(tag):
    return base_path / tag


def assuredir(p):
    if not p.exists():
        os.makedirs(p)


def layout_path(tag, name):
    p = tag_path(tag)
    n = name + ".layout"
    return p / n
    

def purge(wm, tag=None):
    p = tag_path(tag or wm.focused_tag)
    if p.exists():
        os.removedirs(p.resolve())


def read_store(wm, tag=None):
    '''
    Return list of Layouts stored on given or focused tag.
    '''
    p = tag_path(tag or wm.focused_tag)
    if not p.exists():
        return []
    return [Layout(name=one.stem, sexp=one.read_text())
            for one in p.glob("*.layout")]


def add_store(wm, lay, tag=None):
    '''
    Add lay to store for tag
    '''
    lp = layout_path(tag or wm.focused_tag, lay.name)
    assuredir(lp.parent)
    lp.write_text(lay.sexp + "\n")


def del_store(wm, lay, tag=None):
    '''
    Assure layout is no longer in store.
    '''
    tag = tag or wm.focused_tag
    lp = layout_path(tag, lay.name)
    sys.stderr.write(f"dropping {tag}:{lay.name}, {lp}\n")
    os.remove(lp)


def write_store(wm, layouts, tag=None):
    '''
    Save layouts to wm
    '''
    for oen in layouts:
        add_store(wm, one, tag)


def make_icons(oldlays, tag):
    ret = list()
    for lay in oldlays:
        tree = make_tree(lay.sexp)
        iname = f'herbie{tag}{lay.name}'
        fname = make_icon(iname, tree)
        ret.append(iname)
    return ret


def rofi(wm, tag, oldlays, cursexp=None):
    '''Return text rendered for rofi representing stored and current layout.

    If cursexp is given and it matches and existing saved tree
    then the render will emphasize this.
    '''
    lines = []
    index = dict()
    for lay in oldlays:

        #print ("cur:",cursexp)
        #print ("lay:",lay.sexp)
        # if cursexp and cursexp == lay.sexp:
        #     lname = f'<span color="green">{lay.name}</span>'
        # else:
        #     lname = f'<span color="red">{lay.name}</span>'
        lname = lay.name

        tree = make_tree(lay.sexp)
        iname = f'herbie{tag}{lay.name}'
        fname = make_icon(iname, tree)
        line = f'{lname}{NUL}icon{US}{iname}{NUL}name{US}{lay.name}'
        lines.append(line)
        index[lname] = lay
    return lines, index
